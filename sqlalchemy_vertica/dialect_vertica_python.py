from __future__ import annotations

from typing import Any, Dict, Sequence, Tuple
from sqlalchemy.engine.url import URL

from .base import VerticaDialect as BaseVerticaDialect


class VerticaDialect(BaseVerticaDialect):
    driver = "vertica_python"
    supports_statement_cache = True

    @classmethod
    def import_dbapi(cls) -> Any:
        import vertica_python
        return vertica_python

    # Maintain backwards compatibility for any legacy callers
    @classmethod
    def dbapi(cls) -> Any:  # type: ignore[override]
        return cls.import_dbapi()

    def create_connect_args(self, url: URL) -> Tuple[Sequence[Any], Dict[str, Any]]:
        opts: Dict[str, Any] = {}

        if url.host:
            opts["host"] = url.host
        if url.port is not None:
            try:
                opts["port"] = int(url.port)
            except (ValueError, TypeError):
                opts["port"] = url.port
        else:
            opts["port"] = 5433

        if url.username:
            opts["user"] = url.username
        if url.password is not None:
            opts["password"] = url.password
        if url.database:
            opts["database"] = url.database

        # Query options handling
        query = dict(url.query)

        int_keys = {"connection_timeout", "read_timeout", "port"}
        bool_keys = {"autocommit", "connection_load_balance"}

        for key, val in query.items():
            if key in int_keys:
                try:
                    opts[key] = int(val)  # type: ignore[arg-type]
                except (ValueError, TypeError):
                    opts[key] = val
            elif key in bool_keys:
                if isinstance(val, str):
                    opts[key] = val.lower() in ("true", "1", "yes", "on")
                else:
                    opts[key] = bool(val)
            else:
                opts[key] = val

        return [], opts
