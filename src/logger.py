"""
Logger module - drop-in replacement for Python's logging.
Writes to a shared SQLite database.
"""

import sys
import os
import logging as _stdlib_logging
from datetime import datetime
from pathlib import Path
from typing import Any
import threading

CONFIG_BASE = Path.home() / ".config" / "mcp-logger"

_default_repo = None
_lock = threading.Lock()


def get_db_path(logger_name: str) -> Path:
    """Get DB path for a logger. Each logger gets its own DB."""
    return CONFIG_BASE / logger_name / "db"


class SQLiteHandler(_stdlib_logging.Handler):
    """Handler that writes logs to SQLite."""

    def __init__(self, repo: str | None = None, logger_name: str | None = None):
        super().__init__()
        self.repo = repo
        self.logger_name = logger_name

    def emit(self, record: _stdlib_logging.LogRecord) -> None:
        try:
            msg = self.format(record)
            level = record.levelname.lower()
            repo = getattr(record, "repo", self.repo) or _default_repo or "default"
            source = getattr(record, "source", "application")
            metadata = getattr(record, "metadata", None)

            _write_log(
                message=msg,
                level=level,
                repo=repo,
                source=source,
                metadata=metadata,
                logger_name=self.logger_name,
            )
        except Exception:
            self.handleError(record)


def _write_log(
    message: str,
    level: str = "info",
    repo: str | None = None,
    source: str = "application",
    metadata: dict | None = None,
    logger_name: str | None = None,
) -> None:
    """Write a log entry to the shared database."""
    import json
    import sqlite3

    db = get_db_path(logger_name or repo or "default")
    db.parent.mkdir(parents=True, exist_ok=True)

    with _lock:
        conn = sqlite3.connect(db)
        conn.execute(
            """CREATE TABLE IF NOT EXISTS logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                level TEXT NOT NULL,
                message TEXT NOT NULL,
                repo TEXT,
                source TEXT,
                metadata TEXT
            )"""
        )
        conn.execute(
            """INSERT INTO logs (timestamp, level, message, repo, source, metadata)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (
                datetime.utcnow().isoformat(),
                level,
                message,
                repo,
                source,
                json.dumps(metadata) if metadata else None,
            ),
        )
        conn.commit()
        conn.close()


class Logger(_stdlib_logging.Logger):
    """Logger compatible with stdlib logging, writes to SQLite."""

    def __init__(self, name: str, level: int = _stdlib_logging.INFO):
        super().__init__(name, level)
        self._repo = name
        handler = SQLiteHandler(repo=name, logger_name=name)
        handler.setFormatter(_stdlib_logging.Formatter("%(message)s"))
        self.addHandler(handler)

    def set_repo(self, repo: str) -> None:
        """Set the default repo for this logger."""
        self._repo = repo
        for handler in self.handlers:
            if isinstance(handler, SQLiteHandler):
                handler.repo = repo

    def _log_with_repo(
        self,
        level: int,
        msg: str,
        args: tuple,
        repo: str | None = None,
        source: str = "application",
        metadata: dict | None = None,
        **kwargs,
    ) -> None:
        extra = kwargs.pop("extra", {})
        extra["repo"] = repo or self._repo
        extra["source"] = source
        extra["metadata"] = metadata
        super().log(level, msg, *args, extra=extra, **kwargs)

    def debug(
        self,
        msg: str,
        *args,
        repo: str | None = None,
        source: str = "application",
        metadata: dict | None = None,
        **kwargs,
    ) -> None:
        self._log_with_repo(
            _stdlib_logging.DEBUG, msg, args, repo, source, metadata, **kwargs
        )

    def info(
        self,
        msg: str,
        *args,
        repo: str | None = None,
        source: str = "application",
        metadata: dict | None = None,
        **kwargs,
    ) -> None:
        self._log_with_repo(
            _stdlib_logging.INFO, msg, args, repo, source, metadata, **kwargs
        )

    def warning(
        self,
        msg: str,
        *args,
        repo: str | None = None,
        source: str = "application",
        metadata: dict | None = None,
        **kwargs,
    ) -> None:
        self._log_with_repo(
            _stdlib_logging.WARNING, msg, args, repo, source, metadata, **kwargs
        )

    def error(
        self,
        msg: str,
        *args,
        repo: str | None = None,
        source: str = "application",
        metadata: dict | None = None,
        **kwargs,
    ) -> None:
        self._log_with_repo(
            _stdlib_logging.ERROR, msg, args, repo, source, metadata, **kwargs
        )

    def critical(
        self,
        msg: str,
        *args,
        repo: str | None = None,
        source: str = "application",
        metadata: dict | None = None,
        **kwargs,
    ) -> None:
        self._log_with_repo(
            _stdlib_logging.CRITICAL, msg, args, repo, source, metadata, **kwargs
        )

    def exception(
        self,
        msg: str,
        *args,
        repo: str | None = None,
        source: str = "application",
        metadata: dict | None = None,
        **kwargs,
    ) -> None:
        kwargs.setdefault("exc_info", True)
        self._log_with_repo(
            _stdlib_logging.ERROR, msg, args, repo, source, metadata, **kwargs
        )

    def log(
        self,
        level: int,
        msg: str,
        *args,
        repo: str | None = None,
        source: str = "application",
        metadata: dict | None = None,
        **kwargs,
    ) -> None:
        self._log_with_repo(level, msg, args, repo, source, metadata, **kwargs)


_loggers: dict[str, Logger] = {}


def getLogger(name: str) -> Logger:
    """Get or create a logger. Repo defaults to the logger name."""
    if name not in _loggers:
        _loggers[name] = Logger(name)
    return _loggers[name]


get_logger = getLogger


def set_repo(repo: str) -> None:
    """Set the default repo for all loggers."""
    global _default_repo
    _default_repo = repo


def setLevel(level: int) -> None:
    """Set the level for the root logger."""
    _stdlib_logging.getLogger().setLevel(level)


def basicConfig(
    level: int = _stdlib_logging.INFO,
    repo: str | None = None,
    format: str = "%(message)s",
    **kwargs,
) -> None:
    """Configure the root logger."""
    global _default_repo
    if repo:
        _default_repo = repo
    _stdlib_logging.basicConfig(level=level, format=format, **kwargs)


# Import standard logging constants for compatibility
DEBUG = _stdlib_logging.DEBUG
INFO = _stdlib_logging.INFO
WARNING = _stdlib_logging.WARNING
ERROR = _stdlib_logging.ERROR
CRITICAL = _stdlib_logging.CRITICAL


# Also expose the module as 'logging' for easy swapping
logging = sys.modules[__name__]
sys.modules["logging"] = logging
