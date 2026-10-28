from company_brain.ingest import ingest


def doc_paths(con):
    return {r[0] for r in con.execute("SELECT path FROM documents")}


def chunk_count(con):
    return con.execute("SELECT count(*) FROM chunks").fetchone()[0]


def test_ingest_fresh(con, corpus):
    report = ingest(con, corpus, None)
    assert report.added == 2
    assert report.embedded == 0
    assert doc_paths(con) == {"a.md", "sub/b.txt"}


def test_reingest_unchanged(con, corpus):
    ingest(con, corpus, None)
    before = chunk_count(con)
    report = ingest(con, corpus, None)
    assert report.unchanged == 2
    assert chunk_count(con) == before


def fts_hits(con, phrase):
    return con.execute(
        "SELECT count(*) FROM chunks_fts WHERE chunks_fts MATCH ?", (f'"{phrase}"',)
    ).fetchone()[0]


def test_reingest_modified_and_deleted(con, corpus):
    ingest(con, corpus, None)
    assert fts_hits(con, "old phrase") == 1
    (corpus / "a.md").write_text("first line\nbrand new wording\n", encoding="utf-8")
    (corpus / "sub" / "b.txt").unlink()
    report = ingest(con, corpus, None)
    assert report.updated == 1
    assert report.removed == 1
    assert fts_hits(con, "old phrase") == 0
    assert fts_hits(con, "brand new") == 1
    assert doc_paths(con) == {"a.md"}


def test_non_utf8_skipped(con, corpus):
    (corpus / "latin.txt").write_bytes(bytes([0xE9, 0x74, 0xE9]))
    report = ingest(con, corpus, None)
    assert report.skipped == ["latin.txt"]
    assert report.added == 2
