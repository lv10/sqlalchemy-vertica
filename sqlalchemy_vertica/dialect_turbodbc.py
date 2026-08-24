from __future__ import annotations

from typing import Any, Dict, Sequence, Tuple
from sqlalchemy.engine.url import URL

from .base import VerticaDialect as BaseVerticaDialect


class VerticaDialect(BaseVerticaDialect):
    driver = "turbodbc"
    supports_statement_cache = True

    @classmethod
    def import_dbapi(cls) -> Any:
        import turbodbc
        return turbodbc

    def create_connect_args(self, url: URL) -> Tuple[Sequence[Any], Dict[str, Any]]:
        opts: Dict[str, Any] = {}
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
