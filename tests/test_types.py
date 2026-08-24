from __future__ import annotations

from typing import Any
import pytest
import sqlalchemy as sa
from sqlalchemy.types import (
    BIGINT,
    BLOB,
    BOOLEAN,
    CHAR,
    DATE,
    DATETIME,
    DECIMAL,
    FLOAT,
    INTEGER,
    NUMERIC,
    REAL,
    SMALLINT,
    VARCHAR,
)

from sqlalchemy_vertica.base import VerticaDialect
from sqlalchemy_vertica.types import (
    ARRAY,
    BYTEA,
    DOUBLE_PRECISION,
    GEOGRAPHY,
    GEOMETRY,
    INTERVAL,
    LONG_VARBINARY,
    LONG_VARCHAR,
    MAP,
    RAW,
    ROW,
    TIME,
    TIMESTAMPTZ,
    TIMETZ,
    TIMESTAMP,
    UUID,
    VARBINARY,
)


@pytest.fixture
def dialect() -> VerticaDialect:
    return VerticaDialect()


def compile_type(dialect: VerticaDialect, type_engine: Any) -> str:
    return dialect.type_compiler.process(type_engine)


def test_standard_types_compilation(dialect: VerticaDialect) -> None:
    assert compile_type(dialect, INTEGER()) == "INT"
    assert compile_type(dialect, BIGINT()) == "BIGINT"
    assert compile_type(dialect, SMALLINT()) == "SMALLINT"
    assert compile_type(dialect, FLOAT()) == "FLOAT"
    assert compile_type(dialect, FLOAT(precision=24)) == "FLOAT(24)"
    assert compile_type(dialect, DOUBLE_PRECISION()) == "DOUBLE PRECISION"
    assert compile_type(dialect, REAL()) == "REAL"
    assert compile_type(dialect, NUMERIC()) == "NUMERIC"
    assert compile_type(dialect, NUMERIC(10)) == "NUMERIC(10)"
    assert compile_type(dialect, NUMERIC(10, 2)) == "NUMERIC(10, 2)"
    assert compile_type(dialect, DECIMAL(12, 4)) == "NUMERIC(12, 4)"
    assert compile_type(dialect, VARCHAR(100)) == "VARCHAR(100)"
    assert compile_type(dialect, VARCHAR()) == "VARCHAR"
    assert compile_type(dialect, CHAR(10)) == "CHAR(10)"
    assert compile_type(dialect, CHAR()) == "CHAR"
    assert compile_type(dialect, sa.Text()) == "LONG VARCHAR"
    assert compile_type(dialect, BLOB()) == "LONG VARBINARY"
    assert compile_type(dialect, sa.LargeBinary()) == "VARBINARY"
    assert compile_type(dialect, sa.LargeBinary(256)) == "VARBINARY(256)"
    assert compile_type(dialect, BOOLEAN()) == "BOOLEAN"
    assert compile_type(dialect, DATE()) == "DATE"
    assert compile_type(dialect, TIME()) == "TIME"
    assert compile_type(dialect, TIME(precision=6)) == "TIME(6)"
    assert compile_type(dialect, TIME(timezone=True)) == "TIMETZ"
    assert compile_type(dialect, TIMESTAMP()) == "TIMESTAMP"
    assert compile_type(dialect, TIMESTAMP(precision=3)) == "TIMESTAMP(3)"
    assert compile_type(dialect, TIMESTAMP(timezone=True)) == "TIMESTAMPTZ"
    assert compile_type(dialect, DATETIME()) == "DATETIME"


def test_vertica_specific_types_compilation(dialect: VerticaDialect) -> None:
    assert compile_type(dialect, LONG_VARCHAR()) == "LONG VARCHAR"
    assert compile_type(dialect, LONG_VARCHAR(length=65000)) == "LONG VARCHAR(65000)"
    assert compile_type(dialect, LONG_VARBINARY()) == "LONG VARBINARY"
    assert compile_type(dialect, LONG_VARBINARY(length=65000)) == "LONG VARBINARY(65000)"
    assert compile_type(dialect, VARBINARY(128)) == "VARBINARY(128)"
    assert compile_type(dialect, BYTEA()) == "BYTEA"
    assert compile_type(dialect, RAW()) == "RAW"
    assert compile_type(dialect, TIMESTAMPTZ()) == "TIMESTAMPTZ"
    assert compile_type(dialect, TIMESTAMPTZ(precision=6)) == "TIMESTAMPTZ(6)"
    assert compile_type(dialect, TIMETZ()) == "TIMETZ"
    assert compile_type(dialect, TIMETZ(precision=3)) == "TIMETZ(3)"
    assert compile_type(dialect, INTERVAL(fields="DAY TO SECOND")) == "INTERVAL DAY TO SECOND"
    assert compile_type(dialect, INTERVAL(fields="YEAR TO MONTH", precision=2)) == "INTERVAL YEAR TO MONTH (2)"
    assert compile_type(dialect, UUID()) == "UUID"
    assert compile_type(dialect, GEOMETRY()) == "GEOMETRY"
    assert compile_type(dialect, GEOMETRY(srid=4326)) == "GEOMETRY(4326)"
    assert GEOMETRY().get_col_spec() == "GEOMETRY"
    assert GEOMETRY(srid=4326).get_col_spec() == "GEOMETRY(4326)"
    assert compile_type(dialect, GEOGRAPHY()) == "GEOGRAPHY"
    assert compile_type(dialect, GEOGRAPHY(srid=4326)) == "GEOGRAPHY(4326)"
    assert GEOGRAPHY().get_col_spec() == "GEOGRAPHY"
    assert GEOGRAPHY(srid=4326).get_col_spec() == "GEOGRAPHY(4326)"
    assert compile_type(dialect, ARRAY(INTEGER)) == "ARRAY[INT]"
    assert compile_type(dialect, ARRAY(VARCHAR(50), length=5)) == "ARRAY[VARCHAR(50), 5]"
    assert compile_type(dialect, MAP(VARCHAR, INTEGER)) == "MAP[VARCHAR, INT]"
    assert compile_type(dialect, ROW(x=INTEGER, y=VARCHAR(50))) in (
        "ROW(x INT, y VARCHAR(50))",
        "ROW(y VARCHAR(50), x INT)",
    )


def test_column_info_reflection_parsing(dialect: VerticaDialect) -> None:
    # Test numeric with only precision
    info = dialect._get_column_info("amount", "numeric(18)", None, False, "public")
    assert isinstance(info["type"], NUMERIC)
    assert info["type"].precision == 18

    # Test numeric with precision & scale
    info = dialect._get_column_info("price", "numeric(10,2)", None, False, "public")
    assert isinstance(info["type"], NUMERIC)
    assert info["type"].precision == 10
    assert info["type"].scale == 2
    assert info["nullable"] is False

    # Test timestamptz
    info = dialect._get_column_info("created_at", "timestamptz(6)", None, True, "public")
    assert isinstance(info["type"], TIMESTAMPTZ)
    assert info["type"].precision == 6
    assert info["type"].timezone is True

    # Test timestamp without timezone
    info = dialect._get_column_info("updated_at", "timestamp(3)", None, True, "public")
    assert isinstance(info["type"], TIMESTAMP)
    assert info["type"].precision == 3
    assert info["type"].timezone is False

    # Test timetz
    info = dialect._get_column_info("event_time", "timetz(3)", None, True, "public")
    assert isinstance(info["type"], TIMETZ)
    assert info["type"].precision == 3
    assert info["type"].timezone is True

    # Test time without timezone
    info = dialect._get_column_info("start_time", "time(2)", None, True, "public")
    assert isinstance(info["type"], TIME)
    assert info["type"].precision == 2
    assert info["type"].timezone is False

    # Test interval
    info = dialect._get_column_info("duration", "interval day to second(6)", None, True, "public")
    assert isinstance(info["type"], INTERVAL)

    # Test geometry
    info = dialect._get_column_info("geom", "geometry(4326)", None, True, "public")
    assert isinstance(info["type"], GEOMETRY)
    assert info["type"].srid == 4326

    # Test geography
    info = dialect._get_column_info("geog", "geography(4326)", None, True, "public")
    assert isinstance(info["type"], GEOGRAPHY)
    assert info["type"].srid == 4326

    # Test varchar with length
    info = dialect._get_column_info("name", "varchar(100)", None, True, "public")
    assert isinstance(info["type"], VARCHAR)
    assert info["type"].length == 100

    # Test autoincrement sequence default
    info = dialect._get_column_info("id", "int", "nextval('user_id_seq')", False, "public")
    assert info["autoincrement"] is True

    # Test identity default
    info = dialect._get_column_info("id2", "int", "IDENTITY(1,1)", False, "public")
    assert info["autoincrement"] is True

    # Test unknown fallback
    with pytest.warns(sa.exc.SAWarning):
        info = dialect._get_column_info("custom", "unknown_type_foo", None, True, "public")
        assert isinstance(info["type"], sa.sql.sqltypes.NullType)
