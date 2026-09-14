

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from livegraph.storage.postgres.models import AgentRun, Message, ResearchSession


class SessionRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_session_by_id(self, session_id: str) -> ResearchSession | None:
        result = await self.db.execute(
            select(ResearchSession).where(ResearchSession.session_id == session_id)
        )
        return result.scalar_one_or_none()

    async def create_run(self, run_id: str, session_id: int, content: str) -> AgentRun:
        run = AgentRun(id= run_id, session_id= session_id)
        self.db.add(run)
        self.db.add(Message(session_id=session_id, content=content, run_id=run_id, role="user"))
        await self.db.flush()
        return run
        
