from __future__ import annotations

from datetime import UTC, datetime
from typing import Any

from sqlalchemy import JSON, ForeignKey, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


def utc_now_naive() -> datetime:
    return datetime.now(UTC).replace(tzinfo=None)


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


class ResearchSession(Base):
    __tablename__ = "research_sessions"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(unique=True, index=True)
    created_at: Mapped[datetime] = mapped_column(default=utc_now_naive)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "created_at": _iso(self.created_at),
        }


class AgentRun(Base):
    __tablename__ = "agent_runs"

    id: Mapped[str] = mapped_column(primary_key=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    status: Mapped[str] = mapped_column(default="running")
    started_at: Mapped[datetime] = mapped_column(default=utc_now_naive)
    finished_at: Mapped[datetime | None] = mapped_column(default=None)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "status": self.status,
            "started_at": _iso(self.started_at),
            "finished_at": _iso(self.finished_at),
        }


class Message(Base):
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("research_sessions.id"), index=True)
    role: Mapped[str] = mapped_column()
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(default=utc_now_naive)
    run_id: Mapped[str | None] = mapped_column(ForeignKey("agent_runs.id"), default=None, index=True)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "session_id": self.session_id,
            "role": self.role,
            "content": self.content,
            "created_at": _iso(self.created_at),
            "run_id": self.run_id,
        }


class EvaluationRun(Base):
    __tablename__ = "evaluation_runs"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[str] = mapped_column(unique=True, index=True)
    session_id: Mapped[str] = mapped_column(index=True)
    status: Mapped[str] = mapped_column(default="running")
    overall_score: Mapped[float | None] = mapped_column(default=None)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    total_items: Mapped[int] = mapped_column(default=0)
    completed_items: Mapped[int] = mapped_column(default=0)
    started_at: Mapped[datetime] = mapped_column(default=utc_now_naive)
    completed_at: Mapped[datetime | None] = mapped_column(default=None)

    items: Mapped[list[EvaluationRunItem]] = relationship(back_populates="run", cascade="all, delete-orphan")

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "session_id": self.session_id,
            "status": self.status,
            "overall_score": self.overall_score,
            "metrics": self.metrics or {},
            "total_items": self.total_items,
            "completed_items": self.completed_items,
            "started_at": _iso(self.started_at),
            "completed_at": _iso(self.completed_at),
        }


class EvaluationRunItem(Base):
    __tablename__ = "evaluation_run_items"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    run_id: Mapped[int] = mapped_column(ForeignKey("evaluation_runs.id"), index=True)
    item_index: Mapped[int] = mapped_column()
    query_text: Mapped[str] = mapped_column(Text)
    gold_chunk_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    gold_answer: Mapped[str] = mapped_column(Text)
    generated_answer: Mapped[str | None] = mapped_column(Text, default=None)
    retrieved_chunk_ids: Mapped[list[str]] = mapped_column(JSON, default=list)
    metrics: Mapped[dict[str, Any] | None] = mapped_column(JSON, default=None)
    created_at: Mapped[datetime] = mapped_column(default=utc_now_naive)

    run: Mapped[EvaluationRun] = relationship(back_populates="items")

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_index": self.item_index,
            "query_text": self.query_text,
            "gold_chunk_ids": self.gold_chunk_ids or [],
            "gold_answer": self.gold_answer,
            "generated_answer": self.generated_answer,
            "retrieved_chunk_ids": self.retrieved_chunk_ids or [],
            "metrics": self.metrics or {},
        }
