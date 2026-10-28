import pytest

from company_brain.ingest import ingest
from company_brain.search import search

MAXD = 1.2


def test_fts_only_hit(con, kb):
    ingest(con, kb, None)
    hits = search(con, "sick leave", None, max_distance=MAXD)
    assert hits[0].path == "leave.md"
    assert "fts" in hits[0].sources


def test_citation_lines_match_file(con, kb, fake_embedder):
    ingest(con, kb, fake_embedder)
    hits = search(con, "travel costs", fake_embedder, max_distance=MAXD)
    assert hits
    for hit in hits:
        lines = (kb / hit.path).read_text(encoding="utf-8").splitlines()
        cited = "\n".join(lines[hit.line_start - 1 : hit.line_end])
        assert hit.text.strip()[:40] in cited


def test_hybrid_merges_sources(con, kb, fake_embedder):
    ingest(con, kb, fake_embedder)
    hits = search(con, "sick leave policy", fake_embedder, max_distance=MAXD)
    assert hits[0].path == "leave.md"
    assert hits[0].sources == ["fts", "vec"]


def test_no_match_returns_empty(con, kb, fake_embedder):
    ingest(con, kb, fake_embedder)
    assert search(con, "quantum sushi rice", fake_embedder, max_distance=MAXD) == []


@pytest.mark.parametrize("query", ['say "hi', "a*", "AND", "(x"])
def test_fts_syntax_chars_safe(con, kb, query):
    ingest(con, kb, None)
    assert isinstance(search(con, query, None, max_distance=MAXD), list)


def test_cjk_query_no_crash(con, kb):
    ingest(con, kb, None)
    assert isinstance(search(con, "差旅報銷", None, max_distance=MAXD), list)
