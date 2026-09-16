import json
import sys

sys.path.insert(0, "package")

from typing import ClassVar

from livegraph.models.chat import get_chat_model
from livegraph.storage.postgres.manager import get_postgres_manager
from livegraph.storage.postgres.models import AgentRun, Message
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

        result = await db.execute(
            select(Message).where(Message.run_id == run_id, Message.role == "user")
        )
        user_message = result.scalar_one()

    model = get_chat_model()
    reply_text = ""
    async for chunk in model.astream(user_message.content):
        delta = chunk.content if isinstance(chunk.content, str) else str(chunk.content)
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
