"""
SQLite connection and schema bootstrap for Veridict auth.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Default: single file under backend/data/ (directory created on first connect)
_DEFAULT_DB = Path(__file__).resolve().parent.parent / "data" / "veridict_users.db"


def database_path() -> Path:
    raw = os.getenv("DATABASE_PATH", "").strip()
    if raw:
        return Path(raw).expanduser().resolve()
    return _DEFAULT_DB.resolve()


def get_connection() -> sqlite3.Connection:
    path = database_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db() -> None:
    """Create tables from schema.sql if they do not exist."""
    schema_file = Path(__file__).resolve().parent / "schema.sql"
    sql = schema_file.read_text(encoding="utf-8")
    with get_connection() as conn:
        conn.executescript(sql)
        conn.commit()
