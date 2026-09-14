import uuid

from fastapi import APIRouter, Body, HTTPException
from livegraph.repositories.session_repository import SessionRepository
from livegraph.services.run_dispatch import enqueue_agent_run
from livegraph.storage.postgres.manager import get_postgres_manager
from livegraph.storage.postgres.models import ResearchSession

router = APIRouter(prefix="/api/sessions", tags=["sessions"])

@router.post("")
async def create_session():
    manager = get_postgres_manager()
    async with manager.get_session() as db:
        session = ResearchSession(session_id=uuid.uuid4().hex)
        db.add(session)
        await db.commit()
        return session.to_dict()


@router.post("/{session_id}/query")
async def submit_query(session_id: str, content: str = Body(embed=True)):
    manager = get_postgres_manager()
    async with manager.get_session() as db:
        repo = SessionRepository(db)
        session = await repo.get_session_by_id(session_id)
        if session is None:
            raise HTTPException(status_code=404, detail="Session not found")
        run_id = uuid.uuid4().hex
        await repo.create_run(session_id=session.id, run_id=run_id, content=content)
        await db.commit()
    await enqueue_agent_run(run_id)
    return {"run_id": run_id}