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

    context = LiveGraphContext(session_id=research_session.session_id)
    agent = create_agent(
        model=get_chat_model(),
        system_prompt=(
            "You are a live research assistant. For every user question, first call "
            "search_session to check what has already been gathered this session. Then always "
            "call web_search at least once for the topic, even if you already know the answer "
            "from your own training — the user is watching a knowledge graph build from your "
            "searches in real time, so search results matter more than recalled knowledge. "
            "Only skip web_search if search_session already returned content that fully answers "
            "the question. Answer using the retrieved content, and cite what you found."
        ),
        tools=[web_search, search_session],
        context_schema=LiveGraphContext,
    )

    reply_text = ""
    async for mode, chunk in agent.astream(
        {"messages": [{"role": "user", "content": user_message.content}]},
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
