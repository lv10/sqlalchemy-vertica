from __future__ import annotations

from typing import Any

import pytest
from sqlalchemy import Column, ForeignKey, Integer, MetaData, String, Table


class MockCursor:
    def __init__(self, query_handler: Any | None = None) -> None:
        self.query_handler = query_handler
        self.description: list[tuple[Any, ...]] | None = None
        self.rowcount: int = -1
        self.arraysize: int = 1
        self._rows: list[tuple[Any, ...]] = []
        self._closed: bool = False

    def execute(self, operation: Any, parameters: Any | None = None) -> MockCursor:
        if self.query_handler:
            self.description, self._rows = self.query_handler(operation, parameters)
            self.rowcount = len(self._rows)
        else:
            self.description = [("col1", 1, None, None, None, None, None)]
            self._rows = [(1,)]
            self.rowcount = 1
        return self

    def executemany(self, operation: Any, seq_of_parameters: Any) -> MockCursor:
        self.rowcount = len(seq_of_parameters)
        return self

    def fetchone(self) -> tuple[Any, ...] | None:
        if self._rows:
            return self._rows.pop(0)
        return None

    def fetchmany(self, size: int | None = None) -> list[tuple[Any, ...]]:
        if size is None:
            size = self.arraysize
        res = self._rows[:size]
        self._rows = self._rows[size:]
        return res

    def fetchall(self) -> list[tuple[Any, ...]]:
        res = list(self._rows)
        self._rows = []
        return res

    def close(self) -> None:
        self._closed = True


class MockConnection:
    def __init__(self, query_handler: Any | None = None) -> None:
        self.query_handler = query_handler
        self.committed: bool = False
        self.rolled_back: bool = False
        self.closed: bool = False

    def cursor(self, *args: Any, **kwargs: Any) -> MockCursor:
        return MockCursor(self.query_handler)

    def commit(self) -> None:
        self.committed = True

    def rollback(self) -> None:
        self.rolled_back = True

    def close(self) -> None:
        self.closed = True


class MockDBAPI:
    def __init__(self, query_handler: Any | None = None) -> None:
        self.query_handler = query_handler
        self.paramstyle = "named"
        self.Error = Exception
        self.DatabaseError = Exception
        self.DataError = Exception
        self.IntegrityError = Exception
        self.InterfaceError = Exception
        self.InternalError = Exception
        self.NotSupportedError = Exception
        self.OperationalError = Exception
        self.ProgrammingError = Exception
        self.Warning = Exception

    def connect(self, *args: Any, **kwargs: Any) -> MockConnection:
        return MockConnection(self.query_handler)


@pytest.fixture
def mock_dbapi() -> MockDBAPI:
    return MockDBAPI()


@pytest.fixture
def sample_metadata() -> MetaData:
    metadata = MetaData()
    Table(
        "users",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("name", String(50), nullable=False),
        Column("email", String(100), unique=True),
    )
    Table(
        "addresses",
        metadata,
        Column("id", Integer, primary_key=True),
        Column("user_id", Integer, ForeignKey("users.id")),
        Column("address", String(200)),
    )
    return metadata
