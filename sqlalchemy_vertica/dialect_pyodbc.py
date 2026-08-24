from __future__ import annotations

from typing import Any

from sqlalchemy.connectors.pyodbc import PyODBCConnector

from .base import VerticaDialect as BaseVerticaDialect


class VerticaDialect(PyODBCConnector, BaseVerticaDialect):  # type: ignore[misc]
    driver = "pyodbc"
    supports_statement_cache = True

    @classmethod
    def import_dbapi(cls) -> Any:
        return PyODBCConnector.import_dbapi()
