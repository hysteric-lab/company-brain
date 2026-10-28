from __future__ import annotations

import re
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


STOPWORDS = frozenset("""
about all also and any are been being but can could did does doing each for from get
has have how into its many may might much must not our per shall should some such than
that the their then there this too very was were what when where which who whom whose
why will with would you your
""".split())

# FTS errors that mean "this query shape matched nothing", not "the database is broken".
_FTS_QUERY_ERRORS = ("fts5", "syntax error", "unterminated", "no such column")


def _cjk_shingles(query: str) -> list[str]:
    """Overlapping 3-grams of a no-space query (CJK), punctuation removed."""
    q = re.sub(r"\W", "", query)
    return [q[i:i + 3] for i in range(len(q) - 2)] if " " not in query.strip() and len(q) > 4 else []


def fts_match_variants(query: str) -> list[str]:
    """Trigram FTS needs >=3-char contiguous units. Escalate: exact phrase ->
    AND of content words (punctuation and stopwords dropped) -> OR of CJK 3-grams.
    Embedded double quotes are doubled so user input stays a string literal."""
    variants = ['"' + query.replace('"', '""') + '"']
    terms = [t for t in re.findall(r"\w{3,}", query.lower()) if t not in STOPWORDS]
    if terms and " ".join(terms) != query.lower():
        variants.append(" AND ".join(f'"{t}"' for t in terms))
    shingles = _cjk_shingles(query)
    if shingles:
        variants.append(" OR ".join(f'"{s}"' for s in shingles))
    return variants


def fts_search(con: sqlite3.Connection, query: str) -> list[int]:
    """Chunk ids, bm25-ranked, from the first variant that matches. For the CJK
    3-gram variant a chunk must contain at least two thirds of the query's 3-grams:
    questions share boilerplate ("的規定是什麼" is half of "火星移民的規定是什麼"),
    so a keyword hit has to cover most of the question to count as an answer."""
    shingles = _cjk_shingles(query)
    for match in fts_match_variants(query):
        try:
            rows = con.execute(
                "SELECT f.rowid, c.text FROM chunks_fts f JOIN chunks c ON c.id = f.rowid "
                "WHERE chunks_fts MATCH ? ORDER BY bm25(chunks_fts) LIMIT ?",
                (match, CANDIDATES),
            ).fetchall()
        except sqlite3.OperationalError as e:
            if any(k in str(e) for k in _FTS_QUERY_ERRORS):
                continue
            raise
        if shingles and " OR " in match:
            rows = [r for r in rows if sum(s in r[1] for s in shingles) * 3 >= len(shingles) * 2]
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
    merged = rrf_merge(fts_search(con, query), vec_search(con, query, embedder, max_distance))[:top]
    if not merged:
        return []
    # One read for all hits: a chunk deleted by a concurrent ingest is simply absent.
    ids = [cid for cid, _, _ in merged]
    rows = {r[0]: r[1:] for r in con.execute(
        "SELECT c.id, d.path, c.line_start, c.line_end, c.text FROM chunks c "
        f"JOIN documents d ON d.id = c.doc_id WHERE c.id IN ({','.join('?' * len(ids))})",
        ids,
    )}
    return [Hit(*rows[cid], score, sources) for cid, score, sources in merged if cid in rows]
