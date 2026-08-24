from __future__ import annotations

from typing import Any, Optional
import sqlalchemy as sa
from sqlalchemy.engine.url import make_url

from sqlalchemy_vertica.base import VerticaDialect
from sqlalchemy_vertica.dialect_vertica_python import VerticaDialect as VerticaPythonDialect
from sqlalchemy_vertica.dialect_vertica_python_async import (
    VerticaDialect_vertica_python_async as VerticaPythonAsyncDialect,
)
from sqlalchemy_vertica.dialect_pyodbc import VerticaDialect as PyODBCDialect
from sqlalchemy_vertica.dialect_turbodbc import VerticaDialect as TurbodbcDialect


def test_dialect_registry() -> None:
    d_sync = sa.dialects.registry.load("vertica")
    assert issubclass(d_sync, VerticaDialect)

    d_vp = sa.dialects.registry.load("vertica.vertica_python")
    assert issubclass(d_vp, VerticaPythonDialect)

    d_vp_async = sa.dialects.registry.load("vertica.vertica_python_async")
    assert issubclass(d_vp_async, VerticaPythonAsyncDialect)
    assert d_vp_async.is_async is True

    d_async_vp = sa.dialects.registry.load("vertica.async_vertica_python")
    assert issubclass(d_async_vp, VerticaPythonAsyncDialect)

    d_pyodbc = sa.dialects.registry.load("vertica.pyodbc")
    assert issubclass(d_pyodbc, PyODBCDialect)

    d_turbodbc = sa.dialects.registry.load("vertica.turbodbc")
    assert issubclass(d_turbodbc, TurbodbcDialect)


def test_statement_cache_enabled() -> None:
    assert VerticaDialect.supports_statement_cache is True
    assert VerticaPythonDialect.supports_statement_cache is True
    assert VerticaPythonAsyncDialect.supports_statement_cache is True
    assert PyODBCDialect.supports_statement_cache is True
    assert TurbodbcDialect.supports_statement_cache is True


def test_create_connect_args_sync() -> None:
    dialect = VerticaPythonDialect()
    url = make_url(
        "vertica+vertica_python://myuser:mypass@dbhost:5433/mydb"
        "?connection_timeout=15&read_timeout=30&autocommit=true"
        "&connection_load_balance=1&unicode_error=strict&session_label=app1"
    )
    cargs, cparams = dialect.create_connect_args(url)

    assert cargs == []
    assert cparams["host"] == "dbhost"
    assert cparams["port"] == 5433
    assert cparams["user"] == "myuser"
    assert cparams["password"] == "mypass"
    assert cparams["database"] == "mydb"
    assert cparams["connection_timeout"] == 15
    assert cparams["read_timeout"] == 30
    assert cparams["autocommit"] is True
    assert cparams["connection_load_balance"] is True
    assert cparams["unicode_error"] == "strict"
    assert cparams["session_label"] == "app1"


def test_create_connect_args_invalid_int_and_bool() -> None:
    dialect = VerticaPythonDialect()
    url = make_url("vertica+vertica_python://dbhost/mydb?port=invalid&autocommit=false&connection_load_balance=False")
    _, cparams = dialect.create_connect_args(url)
    assert cparams["port"] == "invalid"
    assert cparams["autocommit"] is False
    assert cparams["connection_load_balance"] is False


def test_create_connect_args_default_port() -> None:
    dialect = VerticaPythonDialect()
    url = make_url("vertica+vertica_python://myuser:mypass@dbhost/mydb")
    _, cparams = dialect.create_connect_args(url)
    assert cparams["port"] == 5433


def test_base_dialect_create_connect_args() -> None:
    dialect = VerticaDialect()
    url = make_url("vertica://myuser:mypass@dbhost:5433/mydb?backup_server_node=node2")
    cargs, cparams = dialect.create_connect_args(url)
    assert cargs == []
    assert cparams["user"] == "myuser"
    assert cparams["backup_server_node"] == "node2"


def test_server_version_info_parsing() -> None:
    dialect = VerticaDialect()

    class MockConn:
        def __init__(self, ver_str: Optional[str]) -> None:
            self.ver_str = ver_str

        def scalar(self, stmt: Any, params: Any = None) -> Optional[str]:
            return self.ver_str

    # Test Vertica 24.1
    conn = MockConn("Vertica Analytic Database v24.1.0-0")
    assert dialect._get_server_version_info(conn) == (24, 1, 0)

    # Test Vertica 12.0.4
    conn = MockConn("Vertica Analytic Database v12.0.4-1")
    assert dialect._get_server_version_info(conn) == (12, 0, 4)

    # Test OpenText Vertica 23.4
    conn = MockConn("OpenText Vertica Analytic Database v23.4.0")
    assert dialect._get_server_version_info(conn) == (23, 4, 0)

    # Test Vertica 11.1
    conn = MockConn("Vertica Analytic Database v11.1.1-0")
    assert dialect._get_server_version_info(conn) == (11, 1, 1)

    # Test unknown banner fallback
    conn = MockConn("Custom DB 1.0")
    assert dialect._get_server_version_info(conn) == (0, 0, 0)

    # Test None version
    conn = MockConn(None)
    assert dialect._get_server_version_info(conn) == (0, 0, 0)


def test_default_schema_name() -> None:
    dialect = VerticaDialect()

    class MockConn:
        def scalar(self, stmt: Any, params: Any = None) -> Optional[str]:
            return "analytics"

    conn = MockConn()
    assert dialect._get_default_schema_name(conn) == "analytics"

    class MockConnNone:
        def scalar(self, stmt: Any, params: Any = None) -> Optional[str]:
            return None

    assert dialect._get_default_schema_name(MockConnNone()) == "public"
