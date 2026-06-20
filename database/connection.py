"""
database/connection.py
Database connection management using mysql-connector-python
"""
from __future__ import annotations
import mysql.connector
from mysql.connector import Error
import os


# ── Load .env file manually (no extra dependency needed) ──────────────────────
_env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env")
if os.path.isfile(_env_path):
    with open(_env_path) as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                os.environ.setdefault(_k.strip(), _v.strip().strip("\"'"))


# ── Database configuration ────────────────────────────────────────────────────
DB_CONFIG = {
    "host":     os.getenv("DB_HOST", "localhost"),
    "port":     int(os.getenv("DB_PORT", 3306)),
    "user":     os.getenv("DB_USER", "root"),
    "password": os.getenv("DB_PASS", ""),
    "database": os.getenv("DB_NAME", "evs_pakistan"),
    "autocommit": False,
    "charset":  "utf8mb4",
    "use_unicode": True,
}


class DatabaseConnection:
    """Singleton-style database connection pool manager."""

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._connection = None
        return cls._instance

    def get_connection(self):
        """Return an active MySQL connection, reconnecting if needed."""
        try:
            if self._connection and self._connection.is_connected():
                return self._connection
            self._connection = mysql.connector.connect(**DB_CONFIG)
            return self._connection
        except Error as e:
            raise ConnectionError(f"Cannot connect to database: {e}")

    def close(self):
        """Close the connection cleanly."""
        if self._connection and self._connection.is_connected():
            self._connection.close()
            self._connection = None


# Global helper functions used throughout the application
def get_db():
    """Return the active database connection."""
    return DatabaseConnection().get_connection()


def execute_query(query: str, params: tuple = (), fetch: bool = False,
                  many: bool = False):
    """
    Execute a parameterized query.
    Args:
        query  : SQL string with %s placeholders
        params : tuple of parameter values
        fetch  : if True return rows; else return lastrowid / rowcount
        many   : if True use executemany(params as list of tuples)
    Returns:
        list[dict] when fetch=True, else int (lastrowid or rowcount)
    """
    conn = get_db()
    cursor = conn.cursor(dictionary=True)
    try:
        if many:
            cursor.executemany(query, params)
        else:
            cursor.execute(query, params)

        if fetch:
            result = cursor.fetchall()
        else:
            conn.commit()
            result = cursor.lastrowid or cursor.rowcount

        return result
    except Error as e:
        conn.rollback()
        raise RuntimeError(f"Database error: {e}\nQuery: {query}\nParams: {params}")
    finally:
        cursor.close()


def init_database():
    """
    Create the database and all tables by running schema.sql.
    Called once on first launch.
    """
    import os

    # Connect without selecting a database first
    cfg = {k: v for k, v in DB_CONFIG.items() if k != "database"}
    conn = mysql.connector.connect(**cfg)
    cursor = conn.cursor()

    schema_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "sql", "schema.sql"
    )

    with open(schema_path, "r", encoding="utf-8") as f:
        sql_script = f.read()

    # Split on semicolons, filter empty
    statements = [s.strip() for s in sql_script.split(";") if s.strip()]
    for stmt in statements:
        try:
            cursor.execute(stmt)
            conn.commit()
        except Error as e:
            # Ignore "already exists" errors on re-init
            if e.errno not in (1050, 1060, 1061, 1062):
                print(f"[DB INIT] Warning: {e}")

    cursor.close()
    conn.close()
    print("[DB INIT] Database initialised successfully.")
