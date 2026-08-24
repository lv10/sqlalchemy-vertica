from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from sqlalchemy.engine.url import URL

from .base import VerticaDialect as BaseVerticaDialect


class VerticaDialect(BaseVerticaDialect):
    driver = "turbodbc"
    supports_statement_cache = True

    @classmethod
    def import_dbapi(cls) -> Any:
        import turbodbc
        return turbodbc

    def create_connect_args(self, url: URL) -> tuple[Sequence[Any], dict[str, Any]]:
        opts: dict[str, Any] = {}
        if url.host:
            opts["host"] = url.host
        if url.port is not None:
            opts["port"] = int(url.port)
        else:
            opts["port"] = 5433
        if url.username:
            opts["user"] = url.username
        if url.password is not None:
            opts["password"] = url.password
        if url.database:
            opts["database"] = url.database

        opts.update(url.query)
        return [], opts
