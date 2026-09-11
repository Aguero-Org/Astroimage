from __future__ import annotations

import time
from typing import Any

import structlog
from sqlalchemy import event
from sqlalchemy.engine import Connection
from sqlalchemy.engine.interfaces import DBAPICursor
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from astroimage.config import Settings

logger = structlog.get_logger("astroimage.database")


class Base(DeclarativeBase):
    pass


def _fmt_statement(statement: str) -> str:
    return " ".join(statement.split())


def _attach_query_logging(engine: AsyncEngine) -> None:
    sync_engine = engine.sync_engine

    @event.listens_for(sync_engine, "before_cursor_execute")
    def _before_cursor_execute(
        conn: Connection,
        cursor: DBAPICursor,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        conn.info["astroimage_query_start"] = time.perf_counter()

    @event.listens_for(sync_engine, "after_cursor_execute")
    def _after_cursor_execute(
        conn: Connection,
        cursor: DBAPICursor,
        statement: str,
        parameters: Any,
        context: Any,
        executemany: bool,
    ) -> None:
        start = conn.info.pop("astroimage_query_start", None)
        elapsed_ms = None
        if start is not None:
            elapsed_ms = round((time.perf_counter() - start) * 1000, 2)
        rowcount = -1
        try:
            if cursor.rowcount is not None:
                rowcount = int(cursor.rowcount)
        except Exception:
            rowcount = -1
        logger.info(
            "db_query",
            statement=_fmt_statement(statement),
            rowcount=rowcount,
            executemany=executemany,
            elapsed_ms=elapsed_ms,
        )


def create_engine_from_settings(settings: Settings) -> AsyncEngine:
    engine = create_async_engine(settings.database_url)
    _attach_query_logging(engine)
    return engine


def create_session_factory(engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
