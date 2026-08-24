from __future__ import annotations

from typing import Any

from sqlalchemy import types as sqltypes
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


class LONG_VARCHAR(sqltypes.String):
    __visit_name__ = "LONG_VARCHAR"

    def __init__(self, length: int | None = None, **kwargs: Any) -> None:
        super().__init__(length=length, **kwargs)


class LONG_VARBINARY(sqltypes.LargeBinary):
    __visit_name__ = "LONG_VARBINARY"

    def __init__(self, length: int | None = None, **kwargs: Any) -> None:
        super().__init__(length=length, **kwargs)


class VARBINARY(sqltypes.LargeBinary):
    __visit_name__ = "VARBINARY"

    def __init__(self, length: int | None = None, **kwargs: Any) -> None:
        super().__init__(length=length, **kwargs)


class BYTEA(sqltypes.LargeBinary):
    __visit_name__ = "BYTEA"

    def __init__(self, length: int | None = None, **kwargs: Any) -> None:
        super().__init__(length=length, **kwargs)


class RAW(sqltypes.LargeBinary):
    __visit_name__ = "RAW"

    def __init__(self, length: int | None = None, **kwargs: Any) -> None:
        super().__init__(length=length, **kwargs)


class DOUBLE_PRECISION(sqltypes.Float):
    __visit_name__ = "DOUBLE_PRECISION"

    def __init__(self, precision: int | None = None, **kwargs: Any) -> None:
        super().__init__(precision=precision, **kwargs)


class TIME(sqltypes.TIME):
    __visit_name__ = "TIME"

    def __init__(self, precision: int | None = None, timezone: bool = False, **kwargs: Any) -> None:
        self.precision = precision
        super().__init__(timezone=timezone, **kwargs)


class TIMETZ(sqltypes.TIME):
    __visit_name__ = "TIMETZ"

    def __init__(self, precision: int | None = None, **kwargs: Any) -> None:
        self.precision = precision
        kwargs.pop("timezone", None)
        super().__init__(timezone=True, **kwargs)


class TIMESTAMP(sqltypes.TIMESTAMP):
    __visit_name__ = "TIMESTAMP"

    def __init__(self, precision: int | None = None, timezone: bool = False, **kwargs: Any) -> None:
        self.precision = precision
        super().__init__(timezone=timezone, **kwargs)


class TIMESTAMPTZ(sqltypes.TIMESTAMP):
    __visit_name__ = "TIMESTAMPTZ"

    def __init__(self, precision: int | None = None, **kwargs: Any) -> None:
        self.precision = precision
        kwargs.pop("timezone", None)
        super().__init__(timezone=True, **kwargs)


class GEOMETRY(sqltypes.UserDefinedType):
    __visit_name__ = "GEOMETRY"

    def __init__(self, srid: int | None = None) -> None:
        self.srid = srid

    def get_col_spec(self, **kw: Any) -> str:
        if self.srid is not None:
            return f"GEOMETRY({self.srid})"
        return "GEOMETRY"


class GEOGRAPHY(sqltypes.UserDefinedType):
    __visit_name__ = "GEOGRAPHY"

    def __init__(self, srid: int | None = None) -> None:
        self.srid = srid

    def get_col_spec(self, **kw: Any) -> str:
        if self.srid is not None:
            return f"GEOGRAPHY({self.srid})"
        return "GEOGRAPHY"


class UUID(sqltypes.UUID):
    __visit_name__ = "UUID"


class INTERVAL(sqltypes.TypeEngine):
    __visit_name__ = "INTERVAL"

    def __init__(
        self,
        fields: str | None = None,
        precision: int | None = None,
    ) -> None:
        self.fields = fields
        self.precision = precision


class ARRAY(sqltypes.TypeEngine):
    __visit_name__ = "ARRAY"

    def __init__(
        self,
        item_type: type[sqltypes.TypeEngine] | sqltypes.TypeEngine,
        length: int | None = None,
    ) -> None:
        if isinstance(item_type, type):
            self.item_type = item_type()
        else:
            self.item_type = item_type
        self.length = length


class MAP(sqltypes.TypeEngine):
    __visit_name__ = "MAP"

    def __init__(
        self,
        key_type: type[sqltypes.TypeEngine] | sqltypes.TypeEngine,
        value_type: type[sqltypes.TypeEngine] | sqltypes.TypeEngine,
    ) -> None:
        if isinstance(key_type, type):
            self.key_type = key_type()
        else:
            self.key_type = key_type

        if isinstance(value_type, type):
            self.value_type = value_type()
        else:
            self.value_type = value_type


class ROW(sqltypes.TypeEngine):
    __visit_name__ = "ROW"

    def __init__(self, **fields: type[sqltypes.TypeEngine] | sqltypes.TypeEngine) -> None:
        self.fields = {
            k: v() if isinstance(v, type) else v for k, v in fields.items()
        }


BINARY = VARBINARY

__all__ = [
    "INTEGER",
    "BIGINT",
    "SMALLINT",
    "CHAR",
    "VARCHAR",
    "LONG_VARCHAR",
    "NUMERIC",
    "DECIMAL",
    "FLOAT",
    "REAL",
    "DOUBLE_PRECISION",
    "BOOLEAN",
    "DATE",
    "TIME",
    "TIMETZ",
    "TIMESTAMP",
    "TIMESTAMPTZ",
    "DATETIME",
    "INTERVAL",
    "BLOB",
    "BYTEA",
    "RAW",
    "BINARY",
    "VARBINARY",
    "LONG_VARBINARY",
    "UUID",
    "GEOMETRY",
    "GEOGRAPHY",
    "ARRAY",
    "MAP",
    "ROW",
]
