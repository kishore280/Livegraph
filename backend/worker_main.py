import sys

sys.path.insert(0, "package")

from typing import ClassVar

from sqlalchemy import select

from livegraph.models.chat import get_chat_model
from livegraph.storage.postgres.manager import get_postgres_manager
from livegraph.storage.postgres.models import AgentRun, Message
from livegraph.storage.redis import get_arq_redis_settings


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
    response = await model.ainvoke(user_message.content)
    reply_text = response.content if isinstance(response.content, str) else str(response.content)

    async with manager.get_session() as db:
        db.add(Message(session_id=run.session_id, role="assistant", content=reply_text, run_id=run_id))
        result = await db.execute(select(AgentRun).where(AgentRun.id == run_id))
        run = result.scalar_one()
        run.status = "completed"
        await db.commit()


class WorkerSettings:
    functions: ClassVar[list] = [execute_agent_run]
    redis_settings = get_arq_redis_settings()
