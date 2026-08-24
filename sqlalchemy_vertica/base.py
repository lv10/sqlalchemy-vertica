from __future__ import annotations

import itertools
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple, cast

from sqlalchemy import exc, sql, util
from sqlalchemy.engine import default, reflection
from sqlalchemy.engine.interfaces import (
    ReflectedCheckConstraint,
    ReflectedColumn,
    ReflectedForeignKeyConstraint,
    ReflectedIndex,
    ReflectedPrimaryKeyConstraint,
    ReflectedTableComment,
    ReflectedUniqueConstraint,
)
from sqlalchemy.sql import compiler, sqltypes
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
    TIME,
    TIMESTAMPTZ,
    TIMETZ,
    TIMESTAMP,
    UUID,
    VARBINARY,
)

RESERVED_WORDS = {
    "all", "analyze", "and", "any", "array", "as", "asc", "authorization",
    "between", "bigint", "binary", "bit", "boolean", "both", "by", "case",
    "cast", "char", "character", "check", "coalesce", "collate", "column",
    "constraint", "correlation", "create", "cross", "current_date",
    "current_time", "current_timestamp", "current_user", "date", "decimal",
    "default", "deferrable", "deferred", "delete", "desc", "direct",
    "distinct", "do", "double", "drop", "else", "end", "except", "exists",
    "false", "float", "float8", "for", "foreign", "freeze", "from", "full",
    "function", "grant", "group", "having", "ilike", "in", "initially",
    "inner", "inout", "insert", "instead", "int", "integer", "intersect",
    "interval", "into", "is", "isnull", "join", "ksafe", "leading", "left",
    "like", "limit", "localtime", "localtimestamp", "long", "match",
    "natural", "new", "not", "notnull", "null", "nullif", "number",
    "numeric", "off", "offset", "old", "on", "only", "or", "order", "out",
    "outer", "over", "overlaps", "partition", "placing", "precision",
    "primary", "projection", "raw", "real", "references", "rejected",
    "rename", "replace", "right", "row", "schema", "select", "session_user",
    "set", "setof", "similar", "smallint", "some", "substring", "table",
    "then", "time", "timestamp", "timestamptz", "timetz", "tinyint", "to",
    "trailing", "treat", "true", "truncate", "uncommitted", "union", "unique",
    "unknown", "unsegmented", "update", "user", "using", "uuid", "values",
    "varbinary", "varchar", "varchar2", "varying", "view", "when", "where",
    "with",
}

ischema_names: Dict[str, Any] = {
    "INT": INTEGER,
    "INTEGER": INTEGER,
    "INT8": INTEGER,
    "BIGINT": BIGINT,
    "SMALLINT": SMALLINT,
    "TINYINT": SMALLINT,
    "CHAR": CHAR,
    "VARCHAR": VARCHAR,
    "VARCHAR2": VARCHAR,
    "TEXT": VARCHAR,
    "LONG VARCHAR": LONG_VARCHAR,
    "NUMERIC": NUMERIC,
    "DECIMAL": DECIMAL,
    "NUMBER": NUMERIC,
    "MONEY": NUMERIC,
    "FLOAT": FLOAT,
    "FLOAT8": FLOAT,
    "REAL": REAL,
    "DOUBLE": DOUBLE_PRECISION,
    "DOUBLE PRECISION": DOUBLE_PRECISION,
    "TIMESTAMP": TIMESTAMP,
    "TIMESTAMP WITHOUT TIME ZONE": TIMESTAMP,
    "TIMESTAMP WITH TIMEZONE": TIMESTAMPTZ,
    "TIMESTAMP WITH TIME ZONE": TIMESTAMPTZ,
    "TIMESTAMPTZ": TIMESTAMPTZ,
    "TIME": TIME,
    "TIME WITHOUT TIME ZONE": TIME,
    "TIME WITH TIMEZONE": TIMETZ,
    "TIME WITH TIME ZONE": TIMETZ,
    "TIMETZ": TIMETZ,
    "INTERVAL": INTERVAL,
    "INTERVAL DAY": INTERVAL,
    "INTERVAL DAY TO SECOND": INTERVAL,
    "INTERVAL YEAR TO MONTH": INTERVAL,
    "DATE": DATE,
    "DATETIME": DATETIME,
    "SMALLDATETIME": DATETIME,
    "BINARY": VARBINARY,
    "VARBINARY": VARBINARY,
    "RAW": RAW,
    "BYTEA": BYTEA,
    "BLOB": BLOB,
    "BOOLEAN": BOOLEAN,
    "BOOL": BOOLEAN,
    "LONG VARBINARY": LONG_VARBINARY,
    "GEOMETRY": GEOMETRY,
    "GEOGRAPHY": GEOGRAPHY,
    "UUID": UUID,
    "ARRAY": ARRAY,
    "MAP": MAP,
    "ROW": ROW,
}


class VerticaIdentifierPreparer(compiler.IdentifierPreparer):
    reserved_words = RESERVED_WORDS

    def __init__(self, dialect: default.DefaultDialect, **kw: Any) -> None:
        super().__init__(
            dialect,
            initial_quote='"',
            final_quote='"',
            **kw,
        )


class VerticaTypeCompiler(compiler.GenericTypeCompiler):
    def visit_INTEGER(self, type_: Any, **kw: Any) -> str:
        return "INT"

    def visit_BIGINT(self, type_: Any, **kw: Any) -> str:
        return "BIGINT"

    def visit_SMALLINT(self, type_: Any, **kw: Any) -> str:
        return "SMALLINT"

    def visit_FLOAT(self, type_: Any, **kw: Any) -> str:
        if type_.precision is not None:
            return f"FLOAT({type_.precision})"
        return "FLOAT"

    def visit_DOUBLE_PRECISION(self, type_: Any, **kw: Any) -> str:
        return "DOUBLE PRECISION"

    def visit_REAL(self, type_: Any, **kw: Any) -> str:
        return "REAL"

    def visit_NUMERIC(self, type_: Any, **kw: Any) -> str:
        if type_.precision is None:
            return "NUMERIC"
        if type_.scale is None:
            return f"NUMERIC({type_.precision})"
        return f"NUMERIC({type_.precision}, {type_.scale})"

    def visit_DECIMAL(self, type_: Any, **kw: Any) -> str:
        return self.visit_NUMERIC(type_, **kw)

    def visit_VARCHAR(self, type_: Any, **kw: Any) -> str:
        if type_.length:
            return f"VARCHAR({type_.length})"
        return "VARCHAR"

    def visit_CHAR(self, type_: Any, **kw: Any) -> str:
        if type_.length:
            return f"CHAR({type_.length})"
        return "CHAR"

    def visit_TEXT(self, type_: Any, **kw: Any) -> str:
        return "LONG VARCHAR"

    def visit_LONG_VARCHAR(self, type_: Any, **kw: Any) -> str:
        if type_.length:
            return f"LONG VARCHAR({type_.length})"
        return "LONG VARCHAR"

    def visit_BLOB(self, type_: Any, **kw: Any) -> str:
        return "LONG VARBINARY"

    def visit_VARBINARY(self, type_: Any, **kw: Any) -> str:
        if type_.length:
            return f"VARBINARY({type_.length})"
        return "VARBINARY"

    def visit_LONG_VARBINARY(self, type_: Any, **kw: Any) -> str:
        if type_.length:
            return f"LONG VARBINARY({type_.length})"
        return "LONG VARBINARY"

    def visit_large_binary(self, type_: Any, **kw: Any) -> str:
        if getattr(type_, "length", None):
            return f"VARBINARY({type_.length})"
        return "VARBINARY"

    def visit_BYTEA(self, type_: Any, **kw: Any) -> str:
        return "BYTEA"

    def visit_RAW(self, type_: Any, **kw: Any) -> str:
        return "RAW"

    def visit_BOOLEAN(self, type_: Any, **kw: Any) -> str:
        return "BOOLEAN"

    def visit_DATE(self, type_: Any, **kw: Any) -> str:
        return "DATE"

    def visit_TIME(self, type_: Any, **kw: Any) -> str:
        if getattr(type_, "timezone", False):
            return self.visit_TIMETZ(type_, **kw)
        if getattr(type_, "precision", None) is not None:
            return f"TIME({type_.precision})"
        return "TIME"

    def visit_TIMETZ(self, type_: Any, **kw: Any) -> str:
        if getattr(type_, "precision", None) is not None:
            return f"TIMETZ({type_.precision})"
        return "TIMETZ"

    def visit_TIMESTAMP(self, type_: Any, **kw: Any) -> str:
        if getattr(type_, "timezone", False):
            return self.visit_TIMESTAMPTZ(type_, **kw)
        if getattr(type_, "precision", None) is not None:
            return f"TIMESTAMP({type_.precision})"
        return "TIMESTAMP"

    def visit_TIMESTAMPTZ(self, type_: Any, **kw: Any) -> str:
        if getattr(type_, "precision", None) is not None:
            return f"TIMESTAMPTZ({type_.precision})"
        return "TIMESTAMPTZ"

    def visit_DATETIME(self, type_: Any, **kw: Any) -> str:
        return "DATETIME"

    def visit_INTERVAL(self, type_: Any, **kw: Any) -> str:
        parts = ["INTERVAL"]
        if getattr(type_, "fields", None):
            parts.append(str(type_.fields))
        if getattr(type_, "precision", None) is not None:
            parts.append(f"({type_.precision})")
        return " ".join(parts)

    def visit_UUID(self, type_: Any, **kw: Any) -> str:
        return "UUID"

    def visit_GEOMETRY(self, type_: Any, **kw: Any) -> str:
        if getattr(type_, "srid", None) is not None:
            return f"GEOMETRY({type_.srid})"
        return "GEOMETRY"

    def visit_GEOGRAPHY(self, type_: Any, **kw: Any) -> str:
        if getattr(type_, "srid", None) is not None:
            return f"GEOGRAPHY({type_.srid})"
        return "GEOGRAPHY"

    def visit_ARRAY(self, type_: Any, **kw: Any) -> str:
        inner = self.process(type_.item_type, **kw)
        if getattr(type_, "length", None) is not None:
            return f"ARRAY[{inner}, {type_.length}]"
        return f"ARRAY[{inner}]"

    def visit_MAP(self, type_: Any, **kw: Any) -> str:
        k = self.process(type_.key_type, **kw)
        v = self.process(type_.value_type, **kw)
        return f"MAP[{k}, {v}]"

    def visit_ROW(self, type_: Any, **kw: Any) -> str:
        fields = [
            f"{self.dialect.identifier_preparer.quote(name)} {self.process(ftype, **kw)}"
            for name, ftype in type_.fields.items()
        ]
        return f"ROW({', '.join(fields)})"


class VerticaCompiler(compiler.SQLCompiler):
    def visit_sequence(self, sequence: Any, **kw: Any) -> str:
        seq_name = self.preparer.format_sequence(sequence)
        return f"{seq_name}.NEXTVAL"

    def limit_clause(self, select: Any, **kw: Any) -> str:
        text = ""
        if select._limit_clause is not None:
            text += f" \n LIMIT {self.process(select._limit_clause, **kw)}"
        if select._offset_clause is not None:
            text += f" OFFSET {self.process(select._offset_clause, **kw)}"
        return text

    def for_update_clause(self, select: Any, **kw: Any) -> str:
        return " FOR UPDATE"


class VerticaDDLCompiler(compiler.DDLCompiler):
    def get_column_specification(self, column: Any, **kwargs: Any) -> str:
        colspec = self.preparer.format_column(column)
        colspec += " " + self.dialect.type_compiler.process(column.type)

        if column.primary_key and column is column.table._autoincrement_column:
            colspec += " AUTO_INCREMENT"
        else:
            default_str = self.get_column_default_string(column)
            if default_str is not None:
                colspec += " DEFAULT " + default_str

        if not column.nullable:
            colspec += " NOT NULL"

        return colspec

    def visit_create_index(
        self,
        create: Any,
        include_schema: bool = False,
        include_table_schema: bool = False,
        **kw: Any,
    ) -> str:
        # Vertica is a columnar database using projections; it does not support indexes.
        return ""

    def visit_drop_index(self, drop: Any, **kw: Any) -> str:
        return ""

    def visit_primary_key_constraint(self, constraint: Any, **kw: Any) -> str:
        cols = ", ".join(self.preparer.quote(c.name) for c in constraint.columns)
        text = f"PRIMARY KEY ({cols})"
        if constraint.name:
            text = f"CONSTRAINT {self.preparer.quote(constraint.name)} {text}"
        return text

    def visit_foreign_key_constraint(self, constraint: Any, **kw: Any) -> str:
        cols = ", ".join(self.preparer.quote(c.name) for c in constraint.columns)
        ref_cols = ", ".join(self.preparer.quote(elem.column.name) for elem in constraint.elements)
        ref_table = self.preparer.format_table(constraint.referred_table)
        text = f"FOREIGN KEY ({cols}) REFERENCES {ref_table} ({ref_cols})"
        if constraint.name:
            text = f"CONSTRAINT {self.preparer.quote(constraint.name)} {text}"
        return text

    def visit_unique_constraint(self, constraint: Any, **kw: Any) -> str:
        cols = ", ".join(self.preparer.quote(c.name) for c in constraint.columns)
        text = f"UNIQUE ({cols})"
        if constraint.name:
            text = f"CONSTRAINT {self.preparer.quote(constraint.name)} {text}"
        return text

    def visit_check_constraint(self, constraint: Any, **kw: Any) -> str:
        text = f"CHECK ({self.sql_compiler.process(constraint.sqltext, include_table=False)})"
        if constraint.name:
            text = f"CONSTRAINT {self.preparer.quote(constraint.name)} {text}"
        return text


class VerticaExecutionContext(default.DefaultExecutionContext):
    pass


class VerticaDialect(default.DefaultDialect):
    name = "vertica"
    supports_statement_cache = True

    # Feature capabilities in Vertica
    supports_native_boolean = True
    supports_native_decimal = True
    supports_native_uuid = True
    supports_alter = True
    supports_sequences = True
    supports_identity_columns = True
    supports_comments = True
    supports_schemas = True
    supports_views = True
    supports_multivalues_insert = True
    insert_returning = False
    update_returning = False
    delete_returning = False
    use_insertmanyvalues = False
    postfetch_lastrowid = False
    default_schema_name = "public"

    # Dialect components
    statement_compiler = VerticaCompiler
    ddl_compiler = VerticaDDLCompiler
    type_compiler_cls = VerticaTypeCompiler
    preparer: type[compiler.IdentifierPreparer] = VerticaIdentifierPreparer
    execution_ctx_cls = VerticaExecutionContext
    ischema_names = ischema_names

    def _get_default_schema_name(self, connection: Any) -> str:
        schema = connection.scalar(sql.text("SELECT current_schema()"))
        return str(schema) if schema else "public"

    def _get_server_version_info(self, connection: Any) -> Tuple[int, ...]:
        v = connection.scalar(sql.text("SELECT version()"))
        if not v:
            return (0, 0, 0)
        m = re.search(r"v(\d+)\.(\d+)(?:\.(\d+))?", str(v))
        if m:
            groups = [int(x) for x in m.groups() if x is not None]
            while len(groups) < 3:
                groups.append(0)
            return tuple(groups)
        return (0, 0, 0)

    def create_connect_args(self, url: Any) -> Tuple[Sequence[Any], Dict[str, Any]]:
        opts = url.translate_connect_args(username="user")
        opts.update(url.query)
        return [], opts

    def has_schema(self, connection: Any, schema_name: str, **kw: Any) -> bool:
        stmt = sql.text(
            "SELECT EXISTS ("
            "  SELECT schema_name FROM v_catalog.schemata "
            "  WHERE lower(schema_name) = lower(:schema)"
            ")"
        )
        res = connection.scalar(stmt, {"schema": schema_name})
        return bool(res)

    def has_table(
        self, connection: Any, table_name: str, schema: Optional[str] = None, **kw: Any
    ) -> bool:
        if schema is None:
            schema = self._get_default_schema_name(connection)

        stmt = sql.text(
            "SELECT EXISTS ("
            "  SELECT table_name FROM v_catalog.all_tables "
            "  WHERE lower(table_name) = lower(:table) "
            "    AND lower(schema_name) = lower(:schema)"
            ")"
        )
        res = connection.scalar(stmt, {"table": table_name, "schema": schema})
        return bool(res)

    def has_sequence(
        self, connection: Any, sequence_name: str, schema: Optional[str] = None, **kw: Any
    ) -> bool:
        if schema is None:
            schema = self._get_default_schema_name(connection)

        stmt = sql.text(
            "SELECT EXISTS ("
            "  SELECT sequence_name FROM v_catalog.sequences "
            "  WHERE lower(sequence_name) = lower(:sequence) "
            "    AND lower(sequence_schema) = lower(:schema)"
            ")"
        )
        res = connection.scalar(stmt, {"sequence": sequence_name, "schema": schema})
        return bool(res)

    def has_type(
        self, connection: Any, type_name: str, schema: Optional[str] = None, **kw: Any
    ) -> bool:
        stmt = sql.text(
            "SELECT EXISTS ("
            "  SELECT type_name FROM v_catalog.types "
            "  WHERE lower(type_name) = lower(:type)"
            ")"
        )
        res = connection.scalar(stmt, {"type": type_name})
        return bool(res)

    @reflection.cache
    def get_schema_names(self, connection: Any, **kw: Any) -> List[str]:
        stmt = sql.text(
            "SELECT schema_name FROM v_catalog.schemata "
            "ORDER BY schema_name"
        )
        rows = connection.execute(stmt).fetchall()
        system_schemas = {"v_catalog", "v_monitor", "v_internal", "v_txtindex", "txtindex"}
        return [row[0] for row in rows if row[0].lower() not in system_schemas]

    @reflection.cache
    def get_table_names(
        self, connection: Any, schema: Optional[str] = None, **kw: Any
    ) -> List[str]:
        if schema is not None:
            stmt = sql.text(
                "SELECT table_name FROM v_catalog.tables "
                "WHERE lower(table_schema) = lower(:schema) "
                "  AND NOT is_system_table "
                "ORDER BY table_name"
            )
            rows = connection.execute(stmt, {"schema": schema}).fetchall()
        else:
            stmt = sql.text(
                "SELECT table_name FROM v_catalog.tables "
                "WHERE NOT is_system_table "
                "ORDER BY table_schema, table_name"
            )
            rows = connection.execute(stmt).fetchall()
        return [row[0] for row in rows]

    @reflection.cache
    def get_temp_table_names(
        self, connection: Any, schema: Optional[str] = None, **kw: Any
    ) -> List[str]:
        if schema is not None:
            stmt = sql.text(
                "SELECT table_name FROM v_catalog.tables "
                "WHERE lower(table_schema) = lower(:schema) "
                "  AND is_temp_table "
                "ORDER BY table_name"
            )
            rows = connection.execute(stmt, {"schema": schema}).fetchall()
        else:
            stmt = sql.text(
                "SELECT table_name FROM v_catalog.tables "
                "WHERE is_temp_table "
                "ORDER BY table_schema, table_name"
            )
            rows = connection.execute(stmt).fetchall()
        return [row[0] for row in rows]

    @reflection.cache
    def get_view_names(
        self, connection: Any, schema: Optional[str] = None, **kw: Any
    ) -> List[str]:
        if schema is not None:
            stmt = sql.text(
                "SELECT table_name FROM v_catalog.views "
                "WHERE lower(table_schema) = lower(:schema) "
                "  AND NOT is_system_view "
                "ORDER BY table_name"
            )
            rows = connection.execute(stmt, {"schema": schema}).fetchall()
        else:
            stmt = sql.text(
                "SELECT table_name FROM v_catalog.views "
                "WHERE NOT is_system_view "
                "ORDER BY table_schema, table_name"
            )
            rows = connection.execute(stmt).fetchall()
        return [row[0] for row in rows]

    @reflection.cache
    def get_view_definition(
        self,
        connection: Any,
        view_name: str,
        schema: Optional[str] = None,
        **kw: Any,
    ) -> str:
        if schema is None:
            schema = self._get_default_schema_name(connection)

        stmt = sql.text(
            "SELECT view_definition FROM v_catalog.views "
            "WHERE lower(table_name) = lower(:table) "
            "  AND lower(table_schema) = lower(:schema)"
        )
        res = connection.scalar(stmt, {"table": view_name, "schema": schema})
        return str(res) if res is not None else ""

    @reflection.cache
    def get_table_comment(
        self, connection: Any, table_name: str, schema: Optional[str] = None, **kw: Any
    ) -> ReflectedTableComment:
        if schema is None:
            schema = self._get_default_schema_name(connection)

        stmt = sql.text(
            "SELECT comment FROM v_catalog.comments "
            "WHERE object_type = 'TABLE' "
            "  AND lower(object_name) = lower(:table) "
            "  AND lower(object_schema) = lower(:schema)"
        )
        res = connection.scalar(stmt, {"table": table_name, "schema": schema})
        return cast(ReflectedTableComment, {"text": str(res) if res is not None else None})

    @reflection.cache
    def get_table_oid(
        self, connection: Any, table_name: str, schema: Optional[str] = None, **kw: Any
    ) -> int:
        if schema is None:
            schema = self._get_default_schema_name(connection)

        stmt = sql.text(
            "SELECT table_id FROM ("
            "  SELECT table_id, table_name, table_schema FROM v_catalog.tables "
            "  UNION "
            "  SELECT table_id, table_name, table_schema FROM v_catalog.views"
            ") AS a "
            "WHERE lower(a.table_name) = lower(:table) "
            "  AND lower(a.table_schema) = lower(:schema)"
        )
        table_oid = connection.scalar(stmt, {"table": table_name, "schema": schema})
        if table_oid is None:
            raise exc.NoSuchTableError(f"{schema}.{table_name}" if schema else table_name)
        return int(table_oid)

    @reflection.cache
    def get_columns(
        self, connection: Any, table_name: str, schema: Optional[str] = None, **kw: Any
    ) -> List[ReflectedColumn]:
        if schema is None:
            schema = self._get_default_schema_name(connection)

        cols_stmt = sql.text(
            "SELECT column_name, data_type, column_default, is_nullable, ordinal_position "
            "FROM v_catalog.columns "
            "WHERE lower(table_name) = lower(:table) "
            "  AND lower(table_schema) = lower(:schema) "
            "UNION ALL "
            "SELECT column_name, data_type, '' as column_default, true as is_nullable, ordinal_position "
            "FROM v_catalog.view_columns "
            "WHERE lower(table_name) = lower(:table) "
            "  AND lower(table_schema) = lower(:schema) "
            "ORDER BY ordinal_position"
        )
        cols_rows = connection.execute(cols_stmt, {"table": table_name, "schema": schema}).fetchall()

        if not cols_rows:
            if not self.has_table(connection, table_name, schema=schema):
                raise exc.NoSuchTableError(f"{schema}.{table_name}" if schema else table_name)

        pk_stmt = sql.text(
            "SELECT column_name FROM v_catalog.primary_keys "
            "WHERE lower(table_name) = lower(:table) "
            "  AND lower(table_schema) = lower(:schema)"
        )
        pk_columns = {row[0].lower() for row in connection.execute(pk_stmt, {"table": table_name, "schema": schema})}

        comment_stmt = sql.text(
            "SELECT sub_object_name, comment FROM v_catalog.comments "
            "WHERE object_type = 'COLUMN' "
            "  AND lower(object_name) = lower(:table) "
            "  AND lower(object_schema) = lower(:schema)"
        )
        col_comments = {
            row[0].lower(): row[1]
            for row in connection.execute(comment_stmt, {"table": table_name, "schema": schema})
            if row[0] is not None
        }

        columns: List[ReflectedColumn] = []
        for row in cols_rows:
            name = str(row[0])
            dtype = str(row[1]).lower()
            default_val = row[2] if row[2] != "" else None
            is_nullable = bool(row[3])
            primary_key = name.lower() in pk_columns
            comment = col_comments.get(name.lower())

            col_info = self._get_column_info(
                name=name,
                format_type=dtype,
                default=default_val,
                nullable=is_nullable,
                schema=schema,
            )
            col_info["primary_key"] = primary_key
            col_info["comment"] = comment
            columns.append(cast(ReflectedColumn, col_info))

        return columns

    @reflection.cache
    def get_pk_constraint(
        self, connection: Any, table_name: str, schema: Optional[str] = None, **kw: Any
    ) -> ReflectedPrimaryKeyConstraint:
        if schema is None:
            schema = self._get_default_schema_name(connection)

        stmt = sql.text(
            "SELECT constraint_name, column_name FROM v_catalog.primary_keys "
            "WHERE lower(table_name) = lower(:table) "
            "  AND lower(table_schema) = lower(:schema) "
            "ORDER BY ordinal_position"
        )
        rows = connection.execute(stmt, {"table": table_name, "schema": schema}).fetchall()

        if not rows:
            return cast(ReflectedPrimaryKeyConstraint, {"constrained_columns": [], "name": None})

        constraint_name = rows[0][0]
        constrained_columns = [row[1] for row in rows]
        return cast(
            ReflectedPrimaryKeyConstraint,
            {"constrained_columns": constrained_columns, "name": constraint_name},
        )

    @reflection.cache
    def get_foreign_keys(
        self, connection: Any, table_name: str, schema: Optional[str] = None, **kw: Any
    ) -> List[ReflectedForeignKeyConstraint]:
        if schema is None:
            schema = self._get_default_schema_name(connection)

        stmt = sql.text(
            "SELECT constraint_name, column_name, reference_table_schema, "
            "       reference_table_name, reference_column_name "
            "FROM v_catalog.foreign_keys "
            "WHERE lower(table_name) = lower(:table) "
            "  AND lower(table_schema) = lower(:schema) "
            "ORDER BY constraint_name, ordinal_position"
        )
        rows = connection.execute(stmt, {"table": table_name, "schema": schema}).fetchall()

        fkeys: List[ReflectedForeignKeyConstraint] = []
        for name, group in itertools.groupby(rows, key=lambda r: r[0]):
            items = list(group)
            fkeys.append(
                cast(
                    ReflectedForeignKeyConstraint,
                    {
                        "name": name,
                        "constrained_columns": [item[1] for item in items],
                        "referred_schema": items[0][2],
                        "referred_table": items[0][3],
                        "referred_columns": [item[4] for item in items],
                    },
                )
            )
        return fkeys

    @reflection.cache
    def get_unique_constraints(
        self, connection: Any, table_name: str, schema: Optional[str] = None, **kw: Any
    ) -> List[ReflectedUniqueConstraint]:
        if schema is None:
            schema = self._get_default_schema_name(connection)

        stmt = sql.text(
            "SELECT constraint_name, column_name FROM v_catalog.constraint_columns "
            "WHERE lower(table_name) = lower(:table) "
            "  AND lower(table_schema) = lower(:schema) "
            "  AND constraint_type = 'u' "
            "ORDER BY constraint_name, ordinal_position"
        )
        rows = connection.execute(stmt, {"table": table_name, "schema": schema}).fetchall()

        constraints: List[ReflectedUniqueConstraint] = []
        for name, group in itertools.groupby(rows, key=lambda r: r[0]):
            constraints.append(
                cast(
                    ReflectedUniqueConstraint,
                    {
                        "name": name,
                        "column_names": [item[1] for item in group],
                    },
                )
            )
        return constraints

    @reflection.cache
    def get_check_constraints(
        self, connection: Any, table_name: str, schema: Optional[str] = None, **kw: Any
    ) -> List[ReflectedCheckConstraint]:
        if schema is None:
            schema = self._get_default_schema_name(connection)

        stmt = sql.text(
            "SELECT constraint_name, column_name FROM v_catalog.constraint_columns "
            "WHERE lower(table_name) = lower(:table) "
            "  AND lower(table_schema) = lower(:schema) "
            "  AND constraint_type = 'c' "
            "ORDER BY constraint_name"
        )
        rows = connection.execute(stmt, {"table": table_name, "schema": schema}).fetchall()

        return [cast(ReflectedCheckConstraint, {"name": row[0], "sqltext": row[1]}) for row in rows]

    @reflection.cache
    def get_indexes(
        self, connection: Any, table_name: str, schema: Optional[str] = None, **kw: Any
    ) -> List[ReflectedIndex]:
        return []

    def _get_column_info(
        self,
        name: str,
        format_type: str,
        default: Optional[str],
        nullable: bool,
        schema: Optional[str],
    ) -> Dict[str, Any]:
        attype = re.sub(r"\(.*\)", "", format_type).strip()

        charlen_match = re.search(r"\(([\d,]+)\)", format_type)
        charlen = charlen_match.group(1) if charlen_match else None

        args: Tuple[Any, ...] = ()
        kwargs: Dict[str, Any] = {}

        if attype in ("numeric", "decimal"):
            if charlen:
                parts = charlen.split(",")
                if len(parts) == 2:
                    args = (int(parts[0]), int(parts[1]))
                elif len(parts) == 1:
                    args = (int(parts[0]),)
        elif attype in ("timestamptz", "timestamp with time zone", "timestamp with timezone"):
            if charlen:
                args = (int(charlen),)
            attype = "timestamptz"
        elif attype in ("timetz", "time with time zone", "time with timezone"):
            if charlen:
                args = (int(charlen),)
            attype = "timetz"
        elif attype in ("timestamp", "timestamp without time zone"):
            if charlen:
                args = (int(charlen),)
            attype = "timestamp"
        elif attype in ("time", "time without time zone"):
            if charlen:
                args = (int(charlen),)
            attype = "time"
        elif attype.startswith("interval"):
            field_match = re.match(r"interval\s+(.+)", attype, re.I)
            if field_match:
                kwargs["fields"] = field_match.group(1)
            if charlen:
                kwargs["precision"] = int(charlen)
            attype = "interval"
        elif attype in ("geometry", "geography"):
            if charlen:
                kwargs["srid"] = int(charlen)
        elif charlen and "," not in charlen:
            args = (int(charlen),)

        coltype_cls = self.ischema_names.get(attype.upper())
        if coltype_cls:
            try:
                coltype = coltype_cls(*args, **kwargs)
            except Exception:
                try:
                    coltype = coltype_cls()
                except Exception:
                    coltype = sqltypes.NULLTYPE
        else:
            util.warn(f"Did not recognize type '{format_type}' of column '{name}'")
            coltype = sqltypes.NULLTYPE

        autoincrement = False
        if default is not None:
            if "nextval" in default.lower() or "auto_increment" in default.lower() or "identity" in default.lower():
                autoincrement = True

        return {
            "name": name,
            "type": coltype,
            "nullable": nullable,
            "default": default,
            "autoincrement": autoincrement,
        }
