from __future__ import annotations

from typing import Any, List, Optional, Tuple
from unittest.mock import MagicMock, patch
import pytest
from sqlalchemy import pool, text
from sqlalchemy.engine.url import make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from sqlalchemy_vertica.dialect_vertica_python_async import (
    AsyncAdapt_vertica_python_dbapi,
    AsyncVerticaConnection,
    AsyncVerticaCursor,
    VerticaDialect_vertica_python_async,
)


class MockSyncCursorForAsync:
    def __init__(self) -> None:
        self.description = [("val", 1, None, None, None, None, None)]
        self.rowcount = 1
        self.arraysize = 1
        self.closed = False
        self._rows = [(100,), (200,), (300,)]

    def execute(self, operation: Any, parameters: Optional[Any] = None) -> None:
        pass

    def executemany(self, operation: Any, seq_of_parameters: Any) -> None:
        self.rowcount = len(seq_of_parameters)

    def fetchone(self) -> Optional[Tuple[Any, ...]]:
        if self._rows:
            return self._rows.pop(0)
        return None

    def fetchmany(self, size: Optional[int] = None) -> List[Tuple[Any, ...]]:
        if size is None:
            size = self.arraysize
        res = self._rows[:size]
        self._rows = self._rows[size:]
        return res

    def fetchall(self) -> List[Tuple[Any, ...]]:
        res = list(self._rows)
        self._rows = []
        return res

    def close(self) -> None:
        self.closed = True


class FailingCursor(MockSyncCursorForAsync):
    def close(self) -> None:
        raise RuntimeError("Close error")


class MockSyncConnForAsync:
    def __init__(self) -> None:
        self.committed = False
        self.rolled_back = False
        self.closed = False

    def cursor(self, *args: Any, **kwargs: Any) -> MockSyncCursorForAsync:
        return MockSyncCursorForAsync()

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


class FailingConn(MockSyncConnForAsync):
    def close(self) -> None:
        raise RuntimeError("Close conn error")


@pytest.mark.asyncio
async def test_async_cursor_methods() -> None:
    sync_cur = MockSyncCursorForAsync()
    async_cur = AsyncVerticaCursor(sync_cur)

    assert async_cur.description == sync_cur.description
    assert async_cur.rowcount == 1
    assert async_cur.arraysize == 1

    async_cur.arraysize = 2
    assert async_cur.arraysize == 2

    # Context manager test
    async with async_cur as cur:
        await cur.execute("SELECT 1")
        await cur.executemany("INSERT INTO t VALUES (?)", [(1,), (2,)])
        row1 = await cur.fetchone()
        assert row1 == (100,)
        rows = await cur.fetchmany()
        assert rows == [(200,), (300,)]
        all_rows = await cur.fetchall()
        assert all_rows == []

    assert sync_cur.closed is True


@pytest.mark.asyncio
async def test_async_cursor_close_exception() -> None:
    failing_cur = FailingCursor()
    async_cur = AsyncVerticaCursor(failing_cur)
    # Should not raise exception
    await async_cur.close()


@pytest.mark.asyncio
async def test_async_connection_methods() -> None:
    sync_conn = MockSyncConnForAsync()
    async_conn = AsyncVerticaConnection(sync_conn)

    cur = async_conn.cursor()
    assert isinstance(cur, AsyncVerticaCursor)

    await async_conn.commit()
    assert sync_conn.committed is True

    await async_conn.rollback()
    assert sync_conn.rolled_back is True

    await async_conn.close()
    assert sync_conn.closed is True


@pytest.mark.asyncio
async def test_async_connection_close_exception() -> None:
    failing_conn = FailingConn()
    async_conn = AsyncVerticaConnection(failing_conn)
    # Should not raise exception
    await async_conn.close()


def test_async_dialect_pool_and_import() -> None:
    url = make_url("vertica+vertica_python_async://")
    pool_cls = VerticaDialect_vertica_python_async.get_pool_class(url)
    assert pool_cls is pool.AsyncAdaptedQueuePool

    mock_vp = MagicMock()
    with patch.dict("sys.modules", {"vertica_python": mock_vp}):
        dbapi = VerticaDialect_vertica_python_async.import_dbapi()
        assert isinstance(dbapi, AsyncAdapt_vertica_python_dbapi)
        assert hasattr(dbapi, "OperationalError")


@pytest.mark.asyncio
async def test_create_async_engine_execution() -> None:
    mock_vertica = MagicMock()
    mock_vertica.connect.return_value = MockSyncConnForAsync()
    mock_vertica.Error = Exception
    mock_vertica.DatabaseError = Exception
    mock_vertica.OperationalError = Exception
    mock_vertica.IntegrityError = Exception
    mock_vertica.ProgrammingError = Exception

    mock_dbapi = AsyncAdapt_vertica_python_dbapi(mock_vertica)

    engine = create_async_engine(
        "vertica+vertica_python_async://user:pass@localhost:5433/testdb",
        module=mock_dbapi,
    )

    # 1. Test connect and query
    async with engine.connect() as conn:
        res = await conn.execute(text("SELECT 100"))
        row = res.fetchone()
        assert row is not None
        assert row[0] == 100

    # 2. Test transaction begin block
    async with engine.begin() as conn:
        res = await conn.execute(text("SELECT 100"))
        val = res.scalar()
        assert val == 100

    # 3. Test AsyncSession
    async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        sess_res = await session.execute(text("SELECT 100"))
        val = sess_res.scalar()
        assert val == 100

    await engine.dispose()
