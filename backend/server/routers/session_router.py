import json
import uuid

from fastapi import APIRouter, Body, Header, HTTPException
from fastapi.responses import StreamingResponse
from livegraph.repositories.session_repository import SessionRepository
from livegraph.services.run_dispatch import enqueue_agent_run
from livegraph.storage.postgres.manager import get_postgres_manager
from livegraph.storage.postgres.models import ResearchSession
from livegraph.storage.redis import get_async_redis, run_event_stream_key

from server.sse_utils import (
    SSE_HEARTBEAT_SECONDS,
    SSE_MAX_CONNECTION_MINUTES,
    SSE_POLL_INTERVAL_SECONDS,
    format_heartbeat,
    format_sse,
)

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


@router.get("/runs/{run_id}/events")
async def stream_run_events(
    run_id: str,
    after_seq: str = "0-0",
    last_event_id: str | None = Header(default=None, alias="Last-Event-ID"),
):
    cursor = last_event_id or after_seq

    async def event_source():
        redis = get_async_redis()
        last_id = cursor
        elapsed = 0.0

        while elapsed < SSE_MAX_CONNECTION_MINUTES * 60:
            entries = await redis.xread(
                {run_event_stream_key(run_id): last_id}, block=int(SSE_POLL_INTERVAL_SECONDS * 1000), count=50
            )
            if not entries:
                elapsed += SSE_POLL_INTERVAL_SECONDS
                if elapsed % SSE_HEARTBEAT_SECONDS < SSE_POLL_INTERVAL_SECONDS:
                    yield format_heartbeat()
                continue

            for _stream_key, messages in entries:
                for message_id, fields in messages:
                    last_id = message_id
                    payload = json.loads(fields.get("data", "{}"))
                    event_type = payload.pop("event", "message")
                    yield format_sse(payload, event=event_type, event_id=message_id)
                    if event_type == "run-finished":
                        return
            elapsed = 0.0

    return StreamingResponse(
        event_source(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "Connection": "keep-alive", "X-Accel-Buffering": "no"},
    )