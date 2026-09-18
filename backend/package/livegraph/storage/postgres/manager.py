from contextlib import asynccontextmanager
from typing import TYPE_CHECKING

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from livegraph.storage.postgres.models import Base

if TYPE_CHECKING:
    from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver
    from psycopg_pool import AsyncConnectionPool

SCHEMA_VERSION_TABLE = "livegraph_schema_migrations"
BUSINESS_SCHEMA_VERSION = 3

LANGGRAPH_CHECKPOINT_SETUP_LOCK_KEY = 58213904


class PostgresManager:
    def __init__(self, dsn: str):
        self.dsn = dsn
        self.async_engine = create_async_engine(
            dsn,
            pool_pre_ping=True,
            pool_recycle=1800
        )
        self.async_session = async_sessionmaker(
            bind=self.async_engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        self.langgraph_pool: "AsyncConnectionPool | None" = None
        self.langgraph_checkpointer: "AsyncPostgresSaver | None" = None
        self._langgraph_checkpointer_setup = False

    @asynccontextmanager
    async def get_session(self):
        async with self.async_session() as session:
            yield session

    def _ensure_langgraph_pool(self) -> "AsyncConnectionPool":
        if self.langgraph_pool is None:
            from psycopg_pool import AsyncConnectionPool

            langgraph_dsn = self.dsn.replace("+asyncpg", "").replace("+psycopg", "")
            self.langgraph_pool = AsyncConnectionPool(
                conninfo=langgraph_dsn,
                max_size=10,
                open=False,
                kwargs={"autocommit": True},
                check=AsyncConnectionPool.check_connection,
            )
        return self.langgraph_pool

    def get_langgraph_checkpointer(self) -> "AsyncPostgresSaver":
        if self.langgraph_checkpointer is None:
            from langgraph.checkpoint.postgres.aio import AsyncPostgresSaver

            pool = self._ensure_langgraph_pool()
            self.langgraph_checkpointer = AsyncPostgresSaver(pool)  # pyright: ignore[reportArgumentType]
        return self.langgraph_checkpointer

    async def setup_langgraph_checkpointer(self) -> "AsyncPostgresSaver":
        checkpointer = self.get_langgraph_checkpointer()
        pool = self._ensure_langgraph_pool()
        if not self._langgraph_checkpointer_setup:
            if pool.closed:
                await pool.open()
            async with pool.connection() as connection:
                await connection.execute(
                    f"SELECT pg_advisory_lock({LANGGRAPH_CHECKPOINT_SETUP_LOCK_KEY})"  # pyright: ignore[reportCallIssue, reportArgumentType]
                )
                try:
                    await checkpointer.setup()
                finally:
                    cursor = await connection.execute(
                        f"SELECT pg_advisory_unlock({LANGGRAPH_CHECKPOINT_SETUP_LOCK_KEY})"  # pyright: ignore[reportCallIssue, reportArgumentType]
                    )
                    row = await cursor.fetchone()
                    if not row or row[0] is not True:
                        raise RuntimeError("Failed to release LangGraph checkpoint advisory lock")
            self._langgraph_checkpointer_setup = True
        return checkpointer

    @asynccontextmanager
    async def schema_migration_lock(self):
        async with self.async_engine.connect() as conn:
            await conn.execute(text("SELECT pg_advisory_lock(hashtextextended('livegraph:schema-migration', 0))"))
            await conn.commit()
            try:
                yield
            finally:
                unlocked = await conn.scalar(
                    text("SELECT pg_advisory_unlock(hashtextextended('livegraph:schema-migration', 0))")
                )
                await conn.commit()
                if unlocked is not True:
                    await conn.close()
                    raise RuntimeError("Failed to release schema migration advisory lock")

    async def create_schema_version_table(self) -> None:
        async with self.async_engine.begin() as conn:
            await conn.execute(
                text(
                    f"""
                    CREATE TABLE IF NOT EXISTS {SCHEMA_VERSION_TABLE} (
                        domain VARCHAR(32) PRIMARY KEY,
                        version INTEGER NOT NULL CHECK (version > 0),
                        applied_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP
                    )
                    """
                )
            )

    async def get_schema_versions(self) -> dict[str, int]:
        async with self.async_engine.connect() as conn:
            exists = await conn.scalar(
                text("SELECT to_regclass(:table_name) IS NOT NULL"), {"table_name": SCHEMA_VERSION_TABLE}
            )
            if not exists:
                return {}
            rows = await conn.execute(text(f"SELECT domain, version FROM {SCHEMA_VERSION_TABLE}"))
            return {str(row.domain): int(row.version) for row in rows}

    async def record_schema_version(self, domain: str, version: int) -> None:
        async with self.async_engine.begin() as conn:
            await conn.execute(
                text(
                    f"""
                    INSERT INTO {SCHEMA_VERSION_TABLE} (domain, version, applied_at)
                    VALUES (:domain, :version, CURRENT_TIMESTAMP)
                    ON CONFLICT (domain) DO UPDATE SET version = EXCLUDED.version, applied_at = EXCLUDED.applied_at
                    """
                ),
                {"domain": domain, "version": version},
            )

    async def require_current_schema(self) -> None:
        versions = await self.get_schema_versions()
        if versions.get("business") != BUSINESS_SCHEMA_VERSION:
            raise RuntimeError(
                f"Database schema is missing or stale (business={versions.get('business', 'missing')}, "
                f"required {BUSINESS_SCHEMA_VERSION}). Run the storage-migrator first."
            )

    async def create_business_tables(self) -> None:
        async with self.async_engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)


_manager: PostgresManager | None = None


def get_postgres_manager() -> PostgresManager:
    global _manager
    if _manager is None:
        from livegraph.config import settings
        _manager = PostgresManager(settings.postgres_dsn)
    return _manager
