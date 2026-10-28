from __future__ import annotations

import sqlite3
import sys
from dataclasses import dataclass
from typing import TYPE_CHECKING

import sqlite_vec

from .config import CANDIDATES, MAX_VEC_DISTANCE, RRF_K

if TYPE_CHECKING:
    from .embed import Embedder


@dataclass
class Hit:
    path: str
    line_start: int
    line_end: int
    text: str
    score: float
    sources: list[str]


def fts_match_variants(query: str) -> list[str]:
    """Trigram FTS needs >=3-char contiguous units. Escalate: exact phrase ->
    AND of whitespace terms -> OR of CJK 3-gram shingles (no-space queries).
    Embedded double quotes are doubled so user input stays a string literal."""
    query = query.replace('"', '""')
    variants = [f'"{query}"']
    terms = [t for t in query.split() if len(t) >= 3]
    if len(terms) > 1 or (terms and terms[0] != query):
        variants.append(" AND ".join(f'"{t}"' for t in terms))
    if " " not in query and len(query) > 4:
        shingles = [query[i:i + 3] for i in range(0, len(query) - 2, 3)]
        variants.append(" OR ".join(f'"{s}"' for s in shingles))
    return variants


def fts_search(con: sqlite3.Connection, query: str) -> list[int]:
    """Chunk ids, bm25-ranked, from the first variant that matches."""
    for match in fts_match_variants(query):
        try:
            rows = con.execute(
                "SELECT rowid FROM chunks_fts WHERE chunks_fts MATCH ? "
                "ORDER BY bm25(chunks_fts) LIMIT ?",
                (match, CANDIDATES),
            ).fetchall()
        except sqlite3.OperationalError:
            continue
        if rows:
            return [r[0] for r in rows]
    return []


def vec_search(con: sqlite3.Connection, query: str, embedder: Embedder | None,
               max_distance: float) -> list[int]:
    """Chunk ids by KNN distance, dropping anything farther than max_distance."""
    if embedder is None:
        return []
    try:
        emb = embedder.embed([query], "query")[0]
    except Exception as e:
        print(f"(vector search unavailable: {e})", file=sys.stderr)
        return []
    rows = con.execute(
        "SELECT chunk_id, distance FROM vec_chunks WHERE embedding MATCH ? AND k = ? "
        "ORDER BY distance",
        (sqlite_vec.serialize_float32(emb), CANDIDATES),
    ).fetchall()
    return [cid for cid, dist in rows if dist <= max_distance]


def rrf_merge(fts: list[int], vec: list[int]) -> list[tuple[int, float, list[str]]]:
    scores: dict[int, list] = {}
    for source, ranked in (("fts", fts), ("vec", vec)):
        for rank, cid in enumerate(ranked):
            entry = scores.setdefault(cid, [0.0, []])
            entry[0] += 1.0 / (RRF_K + rank + 1)
            entry[1].append(source)
    return sorted(((cid, s, src) for cid, (s, src) in scores.items()), key=lambda e: -e[1])


def search(con: sqlite3.Connection, query: str, embedder: Embedder | None, top: int = 5,
           max_distance: float = MAX_VEC_DISTANCE) -> list[Hit]:
    merged = rrf_merge(fts_search(con, query), vec_search(con, query, embedder, max_distance))
    hits = []
    for cid, score, sources in merged[:top]:
        path, first, last, text = con.execute(
            "SELECT d.path, c.line_start, c.line_end, c.text FROM chunks c "
            "JOIN documents d ON d.id = c.doc_id WHERE c.id = ?",
            (cid,),
        ).fetchone()
        hits.append(Hit(path, first, last, text, score, sources))
    return hits
