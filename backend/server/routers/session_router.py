import uuid

from fastapi import APIRouter
from livegraph.storage.postgres.manager import get_postgres_manager
from livegraph.storage.postgres.models import ResearchSession

router = APIRouter(prefix="api/sessions", tags=["sessions"])

@router.post("/create")
async def create_session():
    manager = get_postgres_manager()
    async with manager.get_session() as db:
        session = ResearchSession(session_id=uuid.uuid4().hex)
        db.add(session)
        await db.commit()
        return session.to_dict()



