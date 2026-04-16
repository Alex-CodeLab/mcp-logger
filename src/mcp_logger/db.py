import sqlite3
import os
from datetime import datetime
from pathlib import Path


CONFIG_BASE = Path.home() / ".config" / "mcp-logger"


def get_db_path(repo: str) -> Path:
    """Get DB path for a repo. Each repo gets its own DB."""
    return CONFIG_BASE / repo / "db"


def get_db(repo: str = "default") -> sqlite3.Connection:
    db_path = get_db_path(repo)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _init_schema(conn)
    return conn


def _init_schema(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT NOT NULL,
            repo TEXT,
            source TEXT,
            metadata TEXT
        )
    """)
    conn.execute(
        "CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs(timestamp DESC)"
    )
    conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_level ON logs(level)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_logs_repo ON logs(repo)")
    conn.commit()


def write_log(
    message: str,
    level: str = "info",
    repo: str = "default",
    source: str = "application",
    metadata: str | None = None,
) -> int:
    conn = get_db(repo)
    cursor = conn.execute(
        """INSERT INTO logs (timestamp, level, message, repo, source, metadata)
           VALUES (?, ?, ?, ?, ?, ?)""",
        (datetime.utcnow().isoformat(), level, message, repo, source, metadata),
    )
    conn.commit()
    return cursor.lastrowid


def read_logs(
    n: int = 10,
    level: str | None = None,
    repo: str = "default",
) -> list[dict]:
    conn = get_db(repo)
    query = "SELECT * FROM logs"
    conditions = []
    params = []

    if level:
        conditions.append("level = ?")
        params.append(level)
    if repo:
        conditions.append("repo = ?")
        params.append(repo)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(n)

    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]


def search_logs(
    search: str,
    level: str | None = None,
    repo: str = "default",
    limit: int = 50,
) -> list[dict]:
    conn = get_db(repo)
    query = "SELECT * FROM logs WHERE message LIKE ?"
    params = [f"%{search}%"]
    conditions = []

    if level:
        conditions.append("level = ?")
        params.append(level)

    if conditions:
        query += " AND " + " AND ".join(conditions)
    query += " ORDER BY timestamp DESC LIMIT ?"
    params.append(limit)

    cursor = conn.execute(query, params)
    return [dict(row) for row in cursor.fetchall()]
