from __future__ import annotations

from typing import Any, Dict, List, Tuple
import pytest
from sqlalchemy import exc
from sqlalchemy.types import INTEGER, VARCHAR

from sqlalchemy_vertica.base import VerticaDialect


class MockConnectionForReflection:
    def __init__(self, routes: Dict[str, Any]) -> None:
        self.routes = routes
        self.executed_queries: List[Tuple[str, Any]] = []

    def execute(self, stmt: Any, params: Any = None) -> MockResult:
        query = str(stmt).strip()
        self.executed_queries.append((query, params))

        for pattern, res in self.routes.items():
            if pattern in query:
                if callable(res):
                    return MockResult(res(query, params))
                return MockResult(res)
        return MockResult([])

    def scalar(self, stmt: Any, params: Any = None) -> Any:
        res = self.execute(stmt, params).fetchall()
        if res and res[0]:
            return res[0][0]
        return None


class MockResult:
    def __init__(self, rows: List[Tuple[Any, ...]]) -> None:
        self._rows = rows

    def fetchall(self) -> List[Tuple[Any, ...]]:
        return list(self._rows)

    def scalar(self) -> Any:
        if self._rows and self._rows[0]:
            return self._rows[0][0]
        return None

    def __iter__(self) -> Any:
        return iter(self._rows)


@pytest.fixture
def dialect() -> VerticaDialect:
    return VerticaDialect()


def test_get_schema_names(dialect: VerticaDialect) -> None:
    conn = MockConnectionForReflection({
        "v_catalog.schemata": [
            ("public",),
            ("analytics",),
            ("v_catalog",),
            ("v_monitor",),
        ]
    })
    schemas = dialect.get_schema_names(conn)
    assert schemas == ["public", "analytics"]


def test_get_table_names(dialect: VerticaDialect) -> None:
    conn_schema = MockConnectionForReflection({
        "v_catalog.tables": [
            ("users",),
            ("orders",),
        ]
    })
    tables = dialect.get_table_names(conn_schema, schema="public")
    assert tables == ["users", "orders"]

    conn_all = MockConnectionForReflection({
        "v_catalog.tables": [
            ("users",),
            ("orders",),
        ]
    })
    tables_all = dialect.get_table_names(conn_all, schema=None)
    assert tables_all == ["users", "orders"]


def test_get_temp_table_names(dialect: VerticaDialect) -> None:
    conn_schema = MockConnectionForReflection({
        "is_temp_table": [
            ("temp_session_data",),
        ]
    })
    temp_tables = dialect.get_temp_table_names(conn_schema, schema="public")
    assert temp_tables == ["temp_session_data"]

    conn_all = MockConnectionForReflection({
        "is_temp_table": [
            ("temp_session_data",),
        ]
    })
    temp_tables_all = dialect.get_temp_table_names(conn_all, schema=None)
    assert temp_tables_all == ["temp_session_data"]


def test_get_view_names_and_definition(dialect: VerticaDialect) -> None:
    conn_schema = MockConnectionForReflection({
        "v_catalog.views": [
            ("active_users_view",),
        ]
    })
    views = dialect.get_view_names(conn_schema, schema="public")
    assert views == ["active_users_view"]

    conn_all = MockConnectionForReflection({
        "v_catalog.views": [
            ("active_users_view",),
        ]
    })
    views_all = dialect.get_view_names(conn_all, schema=None)
    assert views_all == ["active_users_view"]

    conn_def = MockConnectionForReflection({
        "SELECT current_schema()": [("public",)],
        "view_definition": [
            ("SELECT * FROM users WHERE active = true",),
        ]
    })
    vdef = dialect.get_view_definition(conn_def, "active_users_view", schema=None)
    assert vdef == "SELECT * FROM users WHERE active = true"


def test_get_pk_constraint(dialect: VerticaDialect) -> None:
    conn = MockConnectionForReflection({
        "SELECT current_schema()": [("public",)],
        "v_catalog.primary_keys": [
            ("pk_orders", "order_id"),
            ("pk_orders", "item_id"),
        ]
    })
    pk = dialect.get_pk_constraint(conn, "orders", schema=None)
    assert pk["name"] == "pk_orders"
    assert pk["constrained_columns"] == ["order_id", "item_id"]

    # Test empty PK
    conn_empty = MockConnectionForReflection({
        "SELECT current_schema()": [("public",)],
        "v_catalog.primary_keys": []
    })
    pk_empty = dialect.get_pk_constraint(conn_empty, "orders", schema="public")
    assert pk_empty == {"constrained_columns": [], "name": None}


def test_get_foreign_keys(dialect: VerticaDialect) -> None:
    conn = MockConnectionForReflection({
        "SELECT current_schema()": [("public",)],
        "v_catalog.foreign_keys": [
            ("fk_order_user", "user_id", "public", "users", "id"),
        ]
    })
    fks = dialect.get_foreign_keys(conn, "orders", schema=None)
    assert len(fks) == 1
    assert fks[0]["name"] == "fk_order_user"
    assert fks[0]["constrained_columns"] == ["user_id"]
    assert fks[0]["referred_schema"] == "public"
    assert fks[0]["referred_table"] == "users"
    assert fks[0]["referred_columns"] == ["id"]

    # Test empty foreign keys
    conn_empty = MockConnectionForReflection({
        "SELECT current_schema()": [("public",)],
        "v_catalog.foreign_keys": []
    })
    fks_empty = dialect.get_foreign_keys(conn_empty, "orders", schema="public")
    assert fks_empty == []


def test_get_unique_constraints(dialect: VerticaDialect) -> None:
    conn = MockConnectionForReflection({
        "SELECT current_schema()": [("public",)],
        "constraint_type = 'u'": [
            ("uq_user_email", "email"),
        ]
    })
    uqs = dialect.get_unique_constraints(conn, "users", schema=None)
    assert len(uqs) == 1
    assert uqs[0]["name"] == "uq_user_email"
    assert uqs[0]["column_names"] == ["email"]


def test_get_check_constraints(dialect: VerticaDialect) -> None:
    conn = MockConnectionForReflection({
        "SELECT current_schema()": [("public",)],
        "constraint_type = 'c'": [
            ("chk_age", "age >= 18"),
        ]
    })
    chks = dialect.get_check_constraints(conn, "users", schema=None)
    assert len(chks) == 1
    assert chks[0]["name"] == "chk_age"
    assert chks[0]["sqltext"] == "age >= 18"


def test_get_table_comment(dialect: VerticaDialect) -> None:
    conn = MockConnectionForReflection({
        "SELECT current_schema()": [("public",)],
        "v_catalog.comments": [
            ("Main user accounts table",),
        ]
    })
    comment = dialect.get_table_comment(conn, "users", schema=None)
    assert comment == {"text": "Main user accounts table"}


def test_get_indexes(dialect: VerticaDialect) -> None:
    conn = MockConnectionForReflection({})
    assert dialect.get_indexes(conn, "users", schema="public") == []


def test_get_table_oid(dialect: VerticaDialect) -> None:
    conn = MockConnectionForReflection({
        "SELECT current_schema()": [("public",)],
        "SELECT table_id FROM": [
            (45035996273704976,),
        ]
    })
    oid = dialect.get_table_oid(conn, "users", schema=None)
    assert oid == 45035996273704976

    # Test not found
    conn_empty = MockConnectionForReflection({"SELECT table_id FROM": []})
    with pytest.raises(exc.NoSuchTableError):
        dialect.get_table_oid(conn_empty, "nonexistent", schema="public")


def test_get_columns(dialect: VerticaDialect) -> None:
    conn = MockConnectionForReflection({
        "SELECT current_schema()": [("public",)],
        "v_catalog.columns": [
            ("id", "int", "nextval('user_id_seq')", False, 1),
            ("username", "varchar(50)", None, False, 2),
            ("bio", "varchar(500)", "''", True, 3),
        ],
        "v_catalog.primary_keys": [
            ("id",),
        ],
        "v_catalog.comments": [
            ("username", "Unique login handle"),
        ],
    })

    cols = dialect.get_columns(conn, "users", schema=None)
    assert len(cols) == 3

    id_col = cols[0]
    assert id_col["name"] == "id"
    assert isinstance(id_col["type"], INTEGER)
    assert id_col["primary_key"] is True  # type: ignore[typeddict-item]
    assert id_col["autoincrement"] is True
    assert id_col["nullable"] is False

    user_col = cols[1]
    assert user_col["name"] == "username"
    assert isinstance(user_col["type"], VARCHAR)
    assert user_col["type"].length == 50
    assert user_col["comment"] == "Unique login handle"
    assert user_col["primary_key"] is False  # type: ignore[typeddict-item]


def test_get_columns_nonexistent_table(dialect: VerticaDialect) -> None:
    conn = MockConnectionForReflection({
        "v_catalog.columns": [],
        "v_catalog.all_tables": [(False,)],
    })
    with pytest.raises(exc.NoSuchTableError):
        dialect.get_columns(conn, "missing_table", schema="public")


def test_has_table_has_schema_has_sequence(dialect: VerticaDialect) -> None:
    conn = MockConnectionForReflection({
        "SELECT current_schema()": [("public",)],
        "v_catalog.all_tables": [(True,)],
        "v_catalog.schemata": [(True,)],
        "v_catalog.sequences": [(True,)],
        "v_catalog.types": [(True,)],
    })

    assert dialect.has_table(conn, "users", schema=None) is True
    assert dialect.has_schema(conn, "public") is True
    assert dialect.has_sequence(conn, "user_seq", schema=None) is True
    assert dialect.has_type(conn, "geometry") is True
