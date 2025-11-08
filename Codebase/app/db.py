from __future__ import annotations

from pathlib import Path
from typing import Optional

from flask import current_app, g
from psycopg import Connection, connect
from psycopg_pool import ConnectionPool

_POOL_KEY = "db_pool"
_G_CONN_KEY = "db_conn"


class DatabaseNotInitialized(RuntimeError):
    """Raised when the database pool is referenced before init_app runs."""


def init_app(app) -> None:
    """Create the shared connection pool and register cleanup callbacks."""
    conninfo = app.config.get("DATABASE_URL")
    if not conninfo:
        raise RuntimeError("DATABASE_URL is not configured")

    pool = ConnectionPool(
        conninfo=conninfo,
        min_size=1,
        max_size=app.config.get("DB_POOL_SIZE", 5),
        timeout=app.config.get("DB_TIMEOUT", 10.0),
        kwargs={"autocommit": True},
    )
    app.extensions[_POOL_KEY] = pool

    @app.teardown_appcontext
    def _release_connection(_exc: Optional[BaseException]) -> None:
        release_connection()


def _get_pool() -> ConnectionPool:
    pool = current_app.extensions.get(_POOL_KEY)
    if pool is None:
        raise DatabaseNotInitialized(
            "Database pool has not been initialised; call init_app() first."
        )
    return pool


def get_connection() -> Connection:
    """Return a pooled connection stored on the request context."""
    conn = getattr(g, _G_CONN_KEY, None)
    if conn is None:
        pool = _get_pool()
        conn = pool.getconn(timeout=current_app.config.get("DB_TIMEOUT", 10.0))
        setattr(g, _G_CONN_KEY, conn)
    return conn


def release_connection() -> None:
    """Return the request-scoped connection to the pool if it exists."""
    conn = getattr(g, _G_CONN_KEY, None)
    if conn is None:
        return
    delattr(g, _G_CONN_KEY)

    pool = current_app.extensions.get(_POOL_KEY)
    if pool:
        pool.putconn(conn)


def create_schema(app=None) -> None:
    """Execute the DDL statements to set up the core tables."""
    app = app or current_app
    conninfo = app.config.get("DATABASE_URL")
    if not conninfo:
        raise RuntimeError("DATABASE_URL is not configured")

    schema_path = Path(__file__).with_name("schema.sql")
    ddl_sql = schema_path.read_text(encoding="utf-8")

    with connect(conninfo, autocommit=True) as conn:
        conn.execute(ddl_sql)
