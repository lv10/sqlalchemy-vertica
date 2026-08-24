from __future__ import annotations

import logging
from typing import Any

log = logging.getLogger(__name__)

try:
    from alembic.ddl.impl import DefaultImpl

    class VerticaImpl(DefaultImpl):
        __dialect__ = "vertica"
        transactional_ddl = True

        type_synonyms = DefaultImpl.type_synonyms + (
            {"INT", "INTEGER", "INT8", "BIGINT"},
            {"FLOAT", "FLOAT8", "DOUBLE PRECISION", "REAL"},
            {"VARCHAR", "VARCHAR2", "TEXT", "LONG VARCHAR"},
            {"TIMESTAMP", "TIMESTAMP WITHOUT TIME ZONE", "DATETIME", "SMALLDATETIME"},
            {"TIMESTAMPTZ", "TIMESTAMP WITH TIME ZONE", "TIMESTAMP WITH TIMEZONE"},
            {"TIME", "TIME WITHOUT TIME ZONE"},
            {"TIMETZ", "TIME WITH TIME ZONE", "TIME WITH TIMEZONE"},
            {"VARBINARY", "BINARY", "RAW", "BYTEA", "LONG VARBINARY", "BLOB"},
            {"NUMERIC", "DECIMAL", "NUMBER", "MONEY"},
            {"BOOLEAN", "BOOL"},
        )

        def create_index(self, index: Any, **kw: Any) -> None:
            # Vertica is a columnar database using projections; it does not support indexes.
            # We treat this as a safe no-op to allow generic migrations to succeed.
            log.warning(
                "Vertica does not support indexes (projections are used instead). "
                "Ignoring create_index for '%s'.",
                getattr(index, "name", "unnamed"),
            )

        def drop_index(self, index: Any, **kw: Any) -> None:
            log.warning(
                "Vertica does not support indexes. Ignoring drop_index for '%s'.",
                getattr(index, "name", "unnamed"),
            )

except ImportError:  # pragma: no cover
    VerticaImpl = None  # type: ignore[misc,assignment]
