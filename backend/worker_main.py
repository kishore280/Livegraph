import json
import sys

sys.path.insert(0, "package")

from typing import ClassVar

from langchain.agents import create_agent
from langchain_core.messages import AIMessageChunk
from livegraph.agents.context import LiveGraphContext
from livegraph.agents.tools import search_session, web_search
from livegraph.models.chat import get_chat_model
from livegraph.storage.postgres.manager import get_postgres_manager
from livegraph.storage.postgres.models import AgentRun, Message, ResearchSession
from livegraph.storage.redis import (
    get_arq_redis_settings,
    get_async_redis,
    run_event_stream_key,
)
from sqlalchemy import select


async def _publish_event(run_id: str, event_type: str, payload: dict) -> None:
    redis = get_async_redis()
    await redis.xadd(run_event_stream_key(run_id), {"data": json.dumps({"event": event_type, **payload})})


async def execute_agent_run(ctx: dict, run_id: str) -> None:
    manager = get_postgres_manager()
    async with manager.get_session() as db:
        result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalar_one()

        result = await db.execute(select(ResearchSession).where(ResearchSession.id == run.session_id))
        research_session = result.scalar_one()

        result = await db.execute(
            select(Message).where(Message.run_id == run_id, Message.role == "user")
        )
        user_message = result.scalar_one()

    checkpointer = await manager.setup_langgraph_checkpointer()
    context = LiveGraphContext(session_id=research_session.session_id)
    agent = create_agent(
        model=get_chat_model(),
        checkpointer=checkpointer,
        system_prompt=(
            "You are a live research assistant. For every user question, first call "
            "search_session to check what has already been gathered this session. Only call "
            "web_search if search_session has no relevant content for this question — do not "
            "skip web_search just because you already know the answer from your own training; "
            "recalled knowledge does not count as 'relevant content already gathered'. Answer "
            "using the retrieved content in plain prose — do not add your own citation markers, "
            "footnotes, or a sources list; the sources you used are tracked automatically and "
            "shown to the user separately."
        ),
        tools=[web_search, search_session],
        context_schema=LiveGraphContext,
    )

    config = {"configurable": {"thread_id": research_session.session_id}}

    reply_text = ""
    async for mode, chunk in agent.astream(
        {"messages": [{"role": "user", "content": user_message.content}]},
        config=config,
        context=context,
        stream_mode=["updates", "messages"],
    ):
        if mode != "messages":
            continue
        message_chunk, metadata = chunk
        if not isinstance(message_chunk, AIMessageChunk):
            continue
        if metadata.get("langgraph_node") != "model":
            continue
        delta = getattr(message_chunk, "content", "") or ""
        if delta:
            reply_text += delta
            await _publish_event(run_id, "message-delta", {"content": delta})

    seen_urls: set[str] = set()
    sources = [
        s
        for s in context.sources
        if s["url"] not in seen_urls and not seen_urls.add(s["url"])
    ]
    if sources:
        sources_block = "\n\n**Sources**\n" + "\n".join(
            f"- [{s['title'] or s['url']}]({s['url']})" for s in sources
        )
        reply_text += sources_block
        await _publish_event(run_id, "message-delta", {"content": sources_block})

    async with manager.get_session() as db:
        db.add(Message(session_id=run.session_id, role="assistant", content=reply_text, run_id=run_id))
        result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalar_one()
        run.status = "completed"
        await db.commit()

    await _publish_event(run_id, "run-finished", {"status": "completed"})


class WorkerSettings:
    functions: ClassVar[list] = [execute_agent_run]
    redis_settings = get_arq_redis_settings()
