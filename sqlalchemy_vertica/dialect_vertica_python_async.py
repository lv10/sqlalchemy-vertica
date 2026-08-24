from __future__ import annotations

import asyncio
from collections.abc import Sequence
from typing import Any

from sqlalchemy import pool
from sqlalchemy.connectors.asyncio import (
    AsyncAdapt_dbapi_connection,
    AsyncAdapt_dbapi_module,
    await_only,
)
from sqlalchemy.engine.url import URL

from .dialect_vertica_python import VerticaDialect as VerticaDialect_sync


class AsyncVerticaCursor:
    __slots__ = ("_sync_cursor",)

    def __init__(self, sync_cursor: Any) -> None:
        self._sync_cursor = sync_cursor

    async def __aenter__(self) -> AsyncVerticaCursor:
        return self

    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        await self.close()

    @property
    def description(self) -> Any:
        return self._sync_cursor.description

    @property
    def rowcount(self) -> int:
        return getattr(self._sync_cursor, "rowcount", -1)

    @property
    def arraysize(self) -> int:
        return getattr(self._sync_cursor, "arraysize", 1)

    @arraysize.setter
    def arraysize(self, value: int) -> None:
        self._sync_cursor.arraysize = value

    async def execute(self, operation: Any, parameters: Any | None = None) -> Any:
        if parameters is not None:
            return await asyncio.to_thread(self._sync_cursor.execute, operation, parameters)
        return await asyncio.to_thread(self._sync_cursor.execute, operation)

    async def executemany(self, operation: Any, seq_of_parameters: Sequence[Any]) -> Any:
        return await asyncio.to_thread(self._sync_cursor.executemany, operation, seq_of_parameters)

    async def fetchone(self) -> Any | None:
        return await asyncio.to_thread(self._sync_cursor.fetchone)

    async def fetchmany(self, size: int | None = None) -> list[Any]:
        if size is not None:
            return await asyncio.to_thread(self._sync_cursor.fetchmany, size)
        return await asyncio.to_thread(self._sync_cursor.fetchmany)

    async def fetchall(self) -> list[Any]:
        return await asyncio.to_thread(self._sync_cursor.fetchall)

    async def close(self) -> None:
        try:
            await asyncio.to_thread(self._sync_cursor.close)
        except Exception:
            pass

    def __getattr__(self, name: str) -> Any:
        return getattr(self._sync_cursor, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_sync_cursor":
            super().__setattr__(name, value)
        else:
            setattr(self._sync_cursor, name, value)


class AsyncVerticaConnection:
    __slots__ = ("_sync_conn",)

    def __init__(self, sync_conn: Any) -> None:
        self._sync_conn = sync_conn

    def cursor(self, *args: Any, **kwargs: Any) -> Any:
        sync_cur = self._sync_conn.cursor(*args, **kwargs)
        return AsyncVerticaCursor(sync_cur)

    async def commit(self) -> None:
        await asyncio.to_thread(self._sync_conn.commit)

    async def rollback(self) -> None:
        await asyncio.to_thread(self._sync_conn.rollback)

    async def close(self) -> None:
        try:
            await asyncio.to_thread(self._sync_conn.close)
        except Exception:
            pass

    def __getattr__(self, name: str) -> Any:
        return getattr(self._sync_conn, name)

    def __setattr__(self, name: str, value: Any) -> None:
        if name == "_sync_conn":
            super().__setattr__(name, value)
        else:
            setattr(self._sync_conn, name, value)


class AsyncAdapt_vertica_python_dbapi(AsyncAdapt_dbapi_module):
    def __init__(self, vertica_python_module: Any) -> None:
        self.vertica_python = vertica_python_module
        self.paramstyle = "named"
        self._init_dbapi_attributes()

    def _init_dbapi_attributes(self) -> None:
        for name in (
            "DatabaseError",
            "DataError",
            "Error",
            "IntegrityError",
            "InterfaceError",
            "InternalError",
            "NotSupportedError",
            "OperationalError",
            "ProgrammingError",
            "Warning",
        ):
            setattr(self, name, getattr(self.vertica_python, name, Exception))

    async def async_connect(self, *args: Any, **kwargs: Any) -> AsyncVerticaConnection:
        sync_conn = await asyncio.to_thread(self.vertica_python.connect, *args, **kwargs)
        return AsyncVerticaConnection(sync_conn)

    def connect(self, *args: Any, **kwargs: Any) -> AsyncAdapt_dbapi_connection:
        return AsyncAdapt_dbapi_connection(
            self,
            await_only(self.async_connect(*args, **kwargs)),
        )


class VerticaDialect_vertica_python_async(VerticaDialect_sync):
    driver = "vertica_python_async"
    is_async = True
    supports_statement_cache = True
    has_terminate = False

    @classmethod
    def import_dbapi(cls) -> Any:
        import vertica_python
        return AsyncAdapt_vertica_python_dbapi(vertica_python)

    @classmethod
    def get_pool_class(cls, url: URL) -> type[pool.Pool]:
        return pool.AsyncAdaptedQueuePool
