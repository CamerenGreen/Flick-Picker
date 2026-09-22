"""SQLite store for the API and the local demo."""
import os
import sqlite3
from contextlib import contextmanager
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = Path(os.environ.get("DATA_DIR", ROOT / "backend" / "storage"))
DB_PATH = Path(os.environ.get("DB_PATH", DATA_DIR / "flick_picker.sqlite3"))


@contextmanager
def connect():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(DB_PATH)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    try:
        with connection:
            yield connection
    finally:
        connection.close()


def init_db():
    with connect() as connection:
        connection.executescript("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS media (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            source TEXT NOT NULL,
            source_id TEXT NOT NULL,
            media_type TEXT NOT NULL CHECK(media_type IN ('movie', 'tv')),
            title TEXT NOT NULL,
            overview TEXT NOT NULL DEFAULT '',
            genres TEXT NOT NULL DEFAULT '[]',
            tags TEXT NOT NULL DEFAULT '[]',
            year INTEGER,
            poster_path TEXT,
            UNIQUE(source, source_id, media_type)
        );
        CREATE TABLE IF NOT EXISTS viewing_history (
            user_id INTEGER NOT NULL REFERENCES users(id),
            media_id INTEGER NOT NULL REFERENCES media(id),
            rating REAL CHECK(rating IS NULL OR rating BETWEEN 1 AND 5),
            watched_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            PRIMARY KEY (user_id, media_id)
        );
        """)
