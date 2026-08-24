from __future__ import annotations

import pytest
from sqlalchemy import (
    CheckConstraint,
    Column,
    ForeignKey,
    Index,
    Integer,
    MetaData,
    Sequence,
    String,
    Table,
    UniqueConstraint,
    select,
)
from sqlalchemy.schema import CreateIndex, CreateTable, DropIndex

from sqlalchemy_vertica.base import VerticaDialect


@pytest.fixture
def dialect() -> VerticaDialect:
    return VerticaDialect()


def test_create_table_autoincrement(dialect: VerticaDialect) -> None:
    meta = MetaData()
    tbl = Table(
        "users",
        meta,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("name", String(50), nullable=False),
    )
    stmt = str(CreateTable(tbl).compile(dialect=dialect)).strip()
    assert "CREATE TABLE users" in stmt
    assert "id INT AUTO_INCREMENT NOT NULL" in stmt
    assert "name VARCHAR(50) NOT NULL" in stmt
    assert "PRIMARY KEY (id)" in stmt


def test_create_table_with_constraints(dialect: VerticaDialect) -> None:
    meta = MetaData()
    Table(
        "parents",
        meta,
        Column("id", Integer, primary_key=True),
    )
    child = Table(
        "children",
        meta,
        Column("id", Integer, primary_key=True),
        Column("parent_id", Integer, ForeignKey("parents.id", name="fk_child_parent")),
        Column("code", String(20), nullable=False),
        Column("age", Integer),
        UniqueConstraint("code", name="uq_child_code"),
        CheckConstraint("age >= 0", name="chk_age_pos"),
    )

    stmt = str(CreateTable(child).compile(dialect=dialect)).strip()
    assert "CREATE TABLE children" in stmt
    assert "CONSTRAINT fk_child_parent FOREIGN KEY (parent_id) REFERENCES parents (id)" in stmt
    assert "CONSTRAINT uq_child_code UNIQUE (code)" in stmt
    assert "CONSTRAINT chk_age_pos CHECK (age >= 0)" in stmt


def test_index_compilation_is_noop(dialect: VerticaDialect) -> None:
    meta = MetaData()
    tbl = Table("orders", meta, Column("id", Integer, primary_key=True), Column("code", String(20)))
    idx = Index("ix_orders_code", tbl.c.code)

    create_idx_sql = str(CreateIndex(idx).compile(dialect=dialect)).strip()
    assert create_idx_sql == ""

    drop_idx_sql = str(DropIndex(idx).compile(dialect=dialect)).strip()
    assert drop_idx_sql == ""


def test_limit_offset_clause(dialect: VerticaDialect) -> None:
    meta = MetaData()
    tbl = Table("items", meta, Column("id", Integer, primary_key=True), Column("name", String(50)))

    stmt = select(tbl).limit(10).offset(20)
    sql_text = str(stmt.compile(dialect=dialect, compile_kwargs={"literal_binds": True}))
    assert "LIMIT 10" in sql_text
    assert "OFFSET 20" in sql_text


def test_sequence_nextval(dialect: VerticaDialect) -> None:
    seq = Sequence("my_vertica_seq")
    sql_text = str(select(seq.next_value()).compile(dialect=dialect))
    assert "my_vertica_seq.NEXTVAL" in sql_text


def test_for_update_clause(dialect: VerticaDialect) -> None:
    meta = MetaData()
    tbl = Table("accounts", meta, Column("id", Integer, primary_key=True), Column("balance", Integer))
    stmt = select(tbl).with_for_update()
    sql_text = str(stmt.compile(dialect=dialect))
    assert "FOR UPDATE" in sql_text
