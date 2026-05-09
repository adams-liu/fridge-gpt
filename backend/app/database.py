import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator

from .config import get_settings


def _sqlite_path(database_url: str) -> str:
    prefix = "sqlite:///"
    if not database_url.startswith(prefix):
        raise ValueError("Only sqlite:/// database URLs are supported")
    return database_url.removeprefix(prefix)


def get_database_path() -> str:
    return _sqlite_path(get_settings().database_url)


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    db_path = get_database_path()
    if db_path not in {":memory:", ""}:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    try:
        yield connection
        connection.commit()
    finally:
        connection.close()


def init_db() -> None:
    with connect() as connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS checkout_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source TEXT NOT NULL,
                page_url TEXT NOT NULL,
                captured_at TEXT NOT NULL,
                delivered_at TEXT,
                subtotal REAL,
                total REAL,
                items_json TEXT NOT NULL,
                raw_parser_warnings_json TEXT NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        columns = {
            row["name"]
            for row in connection.execute("PRAGMA table_info(checkout_snapshots)")
        }
        if "delivered_at" not in columns:
            connection.execute(
                "ALTER TABLE checkout_snapshots ADD COLUMN delivered_at TEXT"
            )
