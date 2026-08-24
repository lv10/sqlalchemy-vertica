sqlalchemy-vertica
==================

Modern **Vertica Analytic Database** dialect for **SQLAlchemy 2.0+** with full support for **Async operations**, **Alembic migrations**, and modern Python (3.9 - 3.14+).

.. image:: https://img.shields.io/badge/SQLAlchemy-2.0+-blue.svg
    :target: https://www.sqlalchemy.org/
.. image:: https://img.shields.io/badge/python-3.9+-blue.svg
    :target: https://www.python.org/
.. image:: https://img.shields.io/badge/Vertica-11--24+-green.svg
    :target: https://www.vertica.com/
.. image:: https://img.shields.io/badge/license-MIT-green.svg
    :target: https://opensource.org/licenses/MIT
.. image:: https://img.shields.io/badge/Buy%20Me%20a%20Coffee-Donate-yellow.svg
    :target: https://buymeacoffee.com/luisvillamg


Features
--------

* **Full SQLAlchemy 2.0+ Architecture**: Built on ``DefaultDialect`` with query caching (``supports_statement_cache = True``), 2.0 execution semantics, and parameter-bound reflection.
* **First-Class Async Engine Support**: Run queries asynchronously with ``create_async_engine()`` and ``AsyncSession`` via ``vertica+vertica_python_async://`` without blocking the asyncio event loop.
* **Alembic Migrations**: Native ``VerticaImpl`` integration with transactional DDL, type synonym resolution, and index no-op handling (since Vertica utilizes projections).
* **Multi-Driver Support**:
  * ``vertica-python`` (Synchronous pure-Python DBAPI driver)
  * ``vertica-python-async`` (Asynchronous DBAPI adapter for non-blocking asyncio / FastAPI apps)
  * ``pyodbc`` (ODBC driver)
  * ``turbodbc`` (High-speed ODBC driver for Arrow / NumPy / Pandas data workflows)
* **Rich Vertica Data Types**:
  * Geospatial: ``GEOMETRY``, ``GEOGRAPHY``
  * Identifiers: native ``UUID``
  * Large objects: ``LONG VARCHAR``, ``LONG VARBINARY`` (up to 32MB)
  * Complex types: ``ARRAY``, ``MAP``, ``ROW`` (Vertica 10+)
  * Temporal: ``TIMESTAMPTZ``, ``TIMETZ``, ``INTERVAL``
* **Complete Reflection**: Automatic introspection of schemas, tables, temp tables, views, view definitions, columns, primary keys, foreign keys, unique constraints, check constraints, table & column comments.


Installation
------------

Install from PyPI with your desired driver extras:

.. code-block:: bash

    # Pure Python sync driver (recommended for sync applications)
    pip install "sqlalchemy-vertica[vertica-python]"

    # Pure Python async driver (for AsyncEngine / FastAPI / asyncio)
    pip install "sqlalchemy-vertica[asyncio]"

    # ODBC drivers
    pip install "sqlalchemy-vertica[pyodbc]"
    pip install "sqlalchemy-vertica[turbodbc]"

    # Alembic migrations support
    pip install "sqlalchemy-vertica[alembic]"

    # Install all drivers and tools
    pip install "sqlalchemy-vertica[all]"


Connection Strings
------------------

.. code-block:: python

    import sqlalchemy as sa
    from sqlalchemy.ext.asyncio import create_async_engine

    # 1. Async (for FastAPI / asyncio applications)
    async_engine = create_async_engine(
        "vertica+vertica_python_async://user:pwd@host:5433/database?connection_timeout=10"
    )

    # 2. Sync vertica-python
    engine = sa.create_engine(
        "vertica+vertica_python://user:pwd@host:5433/database?connection_timeout=10"
    )

    # 3. PyODBC with connection string
    engine_pyodbc = sa.create_engine(
        "vertica+pyodbc:///?odbc_connect=DSN%3DVerticaDSN"
    )

    # 4. Turbodbc with DSN
    engine_turbodbc = sa.create_engine(
        "vertica+turbodbc:///?DSN=VerticaDSN"
    )


Quick Start
-----------

Synchronous SQLAlchemy 2.0
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    from sqlalchemy import create_engine, text

    engine = create_engine("vertica+vertica_python://user:pwd@localhost:5433/mydb")

    with engine.connect() as conn:
        result = conn.execute(text("SELECT version()"))
        print(result.scalar())

    # Transaction block
    with engine.begin() as conn:
        conn.execute(
            text("INSERT INTO my_table (name) VALUES (:name)"),
            {"name": "Alice"}
        )


Asynchronous SQLAlchemy 2.0 & FastAPI
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

    import asyncio
    from sqlalchemy import text
    from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

    async def main():
        engine = create_async_engine(
            "vertica+vertica_python_async://user:pwd@localhost:5433/mydb",
            pool_size=10,
        )

        async with engine.connect() as conn:
            result = await conn.execute(text("SELECT 1"))
            print(result.scalar())

        # Using AsyncSession
        session_factory = async_sessionmaker(engine, class_=AsyncSession)
        async with session_factory() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM my_table"))
            print("Count:", result.scalar())

        await engine.dispose()

    asyncio.run(main())


Alembic Migrations
------------------

In your Alembic ``env.py``, simply import ``sqlalchemy_vertica``:

.. code-block:: python

    import sqlalchemy_vertica  # Registers VerticaImpl plugin automatically
    from alembic import context

    # configure context
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        transactional_ddl=True,
    )

Vertica does not support traditional B-tree indexes (it utilizes projections). ``sqlalchemy-vertica`` treats index creation/dropping as safe no-ops in migrations to ensure multi-database migration scripts run seamlessly.


Custom Data Types
-----------------

.. code-block:: python

    from sqlalchemy import Column, Integer, Table, MetaData
    from sqlalchemy_vertica import (
        GEOMETRY,
        GEOGRAPHY,
        UUID,
        LONG_VARCHAR,
        ARRAY,
        MAP,
        ROW,
        TIMESTAMPTZ,
    )

    metadata = MetaData()

    places = Table(
        "places",
        metadata,
        Column("id", Integer, primary_key=True, autoincrement=True),
        Column("guid", UUID, nullable=False),
        Column("description", LONG_VARCHAR),
        Column("location", GEOMETRY(srid=4326)),
        Column("tags", ARRAY(LONG_VARCHAR)),
        Column("metadata", MAP(LONG_VARCHAR, LONG_VARCHAR)),
        Column("created_at", TIMESTAMPTZ),
    )


Testing & Coverage
------------------

Run the automated test suite with ``pytest`` and ``pytest-cov``:

.. code-block:: bash

    pytest -v --cov=sqlalchemy_vertica --cov-report=term-missing


Support
-------

If you find this project helpful and want to support its maintenance and development, you can buy me a coffee:

.. image:: https://cdn.buymeacoffee.com/buttons/v2/default-yellow.png
    :target: https://www.buymeacoffee.com/luisvillamg
    :alt: Buy Me A Coffee
    :width: 180px


License
-------

MIT License. See `LICENSE` for details.
