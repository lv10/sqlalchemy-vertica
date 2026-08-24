from __future__ import annotations

import logging
from unittest.mock import MagicMock

import pytest
from sqlalchemy import Column, Index, Integer, MetaData, String, Table

from sqlalchemy_vertica.alembic import VerticaImpl
from sqlalchemy_vertica.base import VerticaDialect


def test_alembic_vertica_impl_registered() -> None:
    try:
        from alembic.ddl.impl import DefaultImpl
        impl_cls = DefaultImpl.get_by_dialect(VerticaDialect())
        assert issubclass(impl_cls, VerticaImpl)
        assert impl_cls.transactional_ddl is True
    except ImportError:
        pytest.skip("Alembic not installed")


def test_alembic_index_operations_are_noops(caplog: pytest.LogCaptureFixture) -> None:
    if VerticaImpl is None:
        pytest.skip("Alembic not installed")

    dialect = VerticaDialect()
    impl = VerticaImpl(
        dialect=dialect,
        connection=MagicMock(),
        as_sql=False,
        transactional_ddl=True,
        output_buffer=None,
        context_opts={},
    )

    meta = MetaData()
    tbl = Table("test_table", meta, Column("id", Integer), Column("name", String(50)))
    idx = Index("ix_test_name", tbl.c.name)

    with caplog.at_level(logging.WARNING):
        impl.create_index(idx)
        assert "Ignoring create_index for 'ix_test_name'" in caplog.text

    caplog.clear()
    with caplog.at_level(logging.WARNING):
        impl.drop_index(idx)
        assert "Ignoring drop_index for 'ix_test_name'" in caplog.text


def test_alembic_type_synonyms() -> None:
    if VerticaImpl is None:
        pytest.skip("Alembic not installed")

    synonyms = VerticaImpl.type_synonyms

    # Check integer synonyms
    assert any({"INT", "INTEGER", "INT8", "BIGINT"}.issubset(s) for s in synonyms)

    # Check float synonyms
    assert any({"FLOAT", "FLOAT8", "DOUBLE PRECISION", "REAL"}.issubset(s) for s in synonyms)

    # Check varchar synonyms
    assert any({"VARCHAR", "VARCHAR2", "TEXT", "LONG VARCHAR"}.issubset(s) for s in synonyms)

    # Check timestamp synonyms
    assert any({"TIMESTAMP", "TIMESTAMP WITHOUT TIME ZONE", "DATETIME", "SMALLDATETIME"}.issubset(s) for s in synonyms)


def test_alembic_migration_operations_simulation() -> None:
    try:
        from alembic.migration import MigrationContext
        from alembic.operations import Operations
    except ImportError:
        pytest.skip("Alembic not installed")

    mock_conn = MagicMock()
    mock_conn.dialect = VerticaDialect()

    ctx = MigrationContext.configure(mock_conn)
    op = Operations(ctx)

    # Test creating a table with op
    op.create_table(
        "users",
        Column("id", Integer, primary_key=True),
        Column("username", String(50)),
    )

    # Test adding a column
    op.add_column("users", Column("email", String(100)))

    # Test dropping a column
    op.drop_column("users", "email")

    # Test creating an index (should be a safe no-op on Vertica)
    op.create_index("ix_users_username", "users", ["username"])
