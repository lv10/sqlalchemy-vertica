from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.engine.url import make_url

from sqlalchemy_vertica.dialect_pyodbc import VerticaDialect as PyODBCDialect
from sqlalchemy_vertica.dialect_turbodbc import VerticaDialect as TurbodbcDialect
from sqlalchemy_vertica.dialect_vertica_python import VerticaDialect as VerticaPythonDialect


def test_vertica_python_driver_import_dbapi() -> None:
    try:
        dbapi = VerticaPythonDialect.import_dbapi()
        assert dbapi is not None
        assert VerticaPythonDialect.dbapi() is dbapi
    except ImportError:
        pytest.skip("vertica-python not installed")


def test_pyodbc_driver_connect_args() -> None:
    dialect = PyODBCDialect()
    url = make_url("vertica+pyodbc:///?odbc_connect=DSN%3DVerticaDSN")
    cargs, cparams = dialect.create_connect_args(url)
    assert cargs == ["DSN=VerticaDSN"] or "DSN=VerticaDSN" in str(cargs) or "DSN=VerticaDSN" in str(cparams)


def test_pyodbc_driver_import_dbapi() -> None:
    mock_pyodbc = MagicMock()
    with patch("sqlalchemy.connectors.pyodbc.PyODBCConnector.import_dbapi", return_value=mock_pyodbc):
        dbapi = PyODBCDialect.import_dbapi()
        assert dbapi is mock_pyodbc


def test_turbodbc_driver_connect_args() -> None:
    dialect = TurbodbcDialect()
    url = make_url("vertica+turbodbc://myuser:mypass@dbhost:5433/mydb?read_buffer_size=5000")
    cargs, cparams = dialect.create_connect_args(url)
    assert cargs == []
    assert cparams["host"] == "dbhost"
    assert cparams["port"] == 5433
    assert cparams["user"] == "myuser"
    assert cparams["password"] == "mypass"
    assert cparams["database"] == "mydb"
    assert cparams["read_buffer_size"] == "5000"


def test_turbodbc_driver_connect_args_defaults() -> None:
    dialect = TurbodbcDialect()
    url = make_url("vertica+turbodbc://")
    cargs, cparams = dialect.create_connect_args(url)
    assert cparams["port"] == 5433


def test_turbodbc_driver_import_dbapi() -> None:
    mock_turbodbc = MagicMock()
    with patch.dict("sys.modules", {"turbodbc": mock_turbodbc}):
        dbapi = TurbodbcDialect.import_dbapi()
        assert dbapi is mock_turbodbc
