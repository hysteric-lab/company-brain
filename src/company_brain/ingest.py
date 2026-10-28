from __future__ import annotations

import hashlib
import sqlite3
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING

from .chunking import chunk_spans, line_range
from .config import SUFFIXES

if TYPE_CHECKING:
    from .embed import Embedder


@dataclass
class IngestReport:
    added: int = 0
    updated: int = 0
    unchanged: int = 0
    removed: int = 0
    skipped: list[str] = field(default_factory=list)
    embedded: int = 0


def _drop_document(con: sqlite3.Connection, doc_id: int) -> None:
    con.execute(
        "DELETE FROM vec_chunks WHERE chunk_id IN (SELECT id FROM chunks WHERE doc_id = ?)",
        (doc_id,),
    )
    con.execute("DELETE FROM documents WHERE id = ?", (doc_id,))


def _insert_document(con: sqlite3.Connection, rel: str, digest: str, text: str) -> None:
    cur = con.execute(
        "INSERT INTO documents(path, sha256, text) VALUES (?, ?, ?)", (rel, digest, text)
    )
    doc_id = cur.lastrowid
    for start, length in chunk_spans(len(text)):
        first, last = line_range(text, start, length)
        con.execute(
            "INSERT INTO chunks(doc_id, start, length, line_start, line_end, text) "
            "VALUES (?, ?, ?, ?, ?, ?)",
            (doc_id, start, length, first, last, text[start - 1 : start - 1 + length]),
        )


def ingest(con: sqlite3.Connection, root: Path, embedder: Embedder | None) -> IngestReport:
    report = IngestReport()
    known = {path: (doc_id, digest) for doc_id, path, digest in
             con.execute("SELECT id, path, sha256 FROM documents")}
    seen: set[str] = set()
    for f in sorted(p for p in root.rglob("*") if p.is_file() and p.suffix.lower() in SUFFIXES):
        rel = f.relative_to(root).as_posix()
        try:
            text = f.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            print(f"(skipped {rel}: not UTF-8)", file=sys.stderr)
            report.skipped.append(rel)
            continue
        seen.add(rel)
        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        if rel in known:
            doc_id, old = known[rel]
            if old == digest:
                report.unchanged += 1
                continue
            _drop_document(con, doc_id)
            report.updated += 1
        else:
            report.added += 1
        _insert_document(con, rel, digest, text)
    for rel, (doc_id, _) in known.items():
        if rel not in seen:
            _drop_document(con, doc_id)
            report.removed += 1
    con.commit()
    return report
