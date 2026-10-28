import sqlite3
from pathlib import Path

import sqlite_vec

from .config import DIM

SCHEMA = f"""
CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY,
    path TEXT UNIQUE NOT NULL,
    sha256 TEXT NOT NULL,
    text TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS chunks (
    id INTEGER PRIMARY KEY,
    doc_id INTEGER NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    start INTEGER NOT NULL,
    length INTEGER NOT NULL,
    line_start INTEGER NOT NULL,
    line_end INTEGER NOT NULL,
    text TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS chunks_fts USING fts5(
    text, content='chunks', content_rowid='id', tokenize='trigram'
);
CREATE TRIGGER IF NOT EXISTS chunks_ai AFTER INSERT ON chunks BEGIN
    INSERT INTO chunks_fts(rowid, text) VALUES (new.id, new.text);
END;
CREATE TRIGGER IF NOT EXISTS chunks_ad AFTER DELETE ON chunks BEGIN
    INSERT INTO chunks_fts(chunks_fts, rowid, text) VALUES ('delete', old.id, old.text);
END;
CREATE VIRTUAL TABLE IF NOT EXISTS vec_chunks USING vec0(
    chunk_id INTEGER PRIMARY KEY, embedding float[{DIM}]
);
"""


def load_vec_extension(con: sqlite3.Connection) -> None:
    if not hasattr(con, "enable_load_extension"):
        raise RuntimeError(
            "This Python's sqlite3 was built without enable_load_extension, so the "
            "sqlite-vec extension cannot load (the python.org macOS installer is one such "
            "build). Use a Python that supports it, e.g. Homebrew's python3 or one "
            "installed with uv (`uv venv --python 3.12`)."
        )
    con.enable_load_extension(True)
    sqlite_vec.load(con)
    con.enable_load_extension(False)


def connect(db_path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(db_path)
    load_vec_extension(con)
    con.execute("PRAGMA foreign_keys=ON")
    con.executescript(SCHEMA)
    return con
