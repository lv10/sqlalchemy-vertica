from __future__ import annotations

from sqlalchemy.dialects import registry

from .base import (
    VerticaCompiler,
    VerticaDDLCompiler,
    VerticaDialect,
    VerticaExecutionContext,
    VerticaIdentifierPreparer,
    VerticaTypeCompiler,
)
from .types import (
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
    TIMESTAMPTZ,
    TIMETZ,
    UUID,
    VARBINARY,
)

__version__ = "1.0.0"

# Register dialects with SQLAlchemy registry
registry.register("vertica", "sqlalchemy_vertica.dialect_vertica_python", "VerticaDialect")
registry.register("vertica.vertica_python", "sqlalchemy_vertica.dialect_vertica_python", "VerticaDialect")
registry.register(
    "vertica.vertica_python_async",
    "sqlalchemy_vertica.dialect_vertica_python_async",
    "VerticaDialect_vertica_python_async",
)
registry.register(
    "vertica.async_vertica_python",
    "sqlalchemy_vertica.dialect_vertica_python_async",
    "VerticaDialect_vertica_python_async",
)
registry.register("vertica.pyodbc", "sqlalchemy_vertica.dialect_pyodbc", "VerticaDialect")
registry.register("vertica.turbodbc", "sqlalchemy_vertica.dialect_turbodbc", "VerticaDialect")

# Try loading alembic plugin if alembic is present
try:
    from . import alembic  # noqa: F401
except Exception:  # pragma: no cover
    pass

__all__ = [
    "__version__",
    "VerticaDialect",
    "VerticaCompiler",
    "VerticaDDLCompiler",
    "VerticaTypeCompiler",
    "VerticaIdentifierPreparer",
    "VerticaExecutionContext",
    "ARRAY",
    "MAP",
    "ROW",
    "UUID",
    "GEOMETRY",
    "GEOGRAPHY",
    "LONG_VARCHAR",
    "LONG_VARBINARY",
    "TIMESTAMPTZ",
    "TIMETZ",
    "INTERVAL",
    "BYTEA",
    "RAW",
    "VARBINARY",
    "DOUBLE_PRECISION",
]
