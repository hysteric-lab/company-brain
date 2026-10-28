import io
import json
import urllib.error

from company_brain import embed
from company_brain.embed import VoyageEmbedder, default_embedder
from company_brain.ingest import ingest


def counts(con):
    chunks = con.execute("SELECT count(*) FROM chunks").fetchone()[0]
    vecs = con.execute("SELECT count(*) FROM vec_chunks").fetchone()[0]
    return chunks, vecs


def test_default_embedder_no_key(monkeypatch, capsys):
    monkeypatch.delenv("VOYAGE_API_KEY", raising=False)
    assert default_embedder() is None
    assert "VOYAGE_API_KEY not set" in capsys.readouterr().err


def test_ingest_writes_vectors(con, corpus, fake_embedder):
    report = ingest(con, corpus, fake_embedder)
    chunks, vecs = counts(con)
    assert report.embedded == chunks == vecs
    assert chunks > 0


def test_reingest_drops_old_vectors(con, corpus, fake_embedder):
    ingest(con, corpus, fake_embedder)
    (corpus / "a.md").write_text("first line\nbrand new wording\n", encoding="utf-8")
    (corpus / "sub" / "b.txt").unlink()
    ingest(con, corpus, fake_embedder)
    chunks, vecs = counts(con)
    assert vecs == chunks


def test_backfill_vectors_after_fts_only(con, corpus, fake_embedder):
    ingest(con, corpus, None)
    report = ingest(con, corpus, fake_embedder)
    chunks, vecs = counts(con)
    assert report.unchanged == 2
    assert report.embedded == chunks == vecs


def test_voyage_retry(monkeypatch):
    calls = {"n": 0}

    def fake_urlopen(req, timeout=None):
        calls["n"] += 1
        if calls["n"] < 3:
            raise urllib.error.HTTPError(req.full_url, 429, "Too Many Requests", {}, None)
        body = json.dumps({"data": [{"embedding": [0.5, 0.5]}]}).encode()
        return io.BytesIO(body)

    monkeypatch.setattr(embed.urllib.request, "urlopen", fake_urlopen)
    monkeypatch.setattr(embed.time, "sleep", lambda s: None)
    vectors = VoyageEmbedder("k").embed(["hello"], "document")
    assert calls["n"] == 3
    assert vectors == [[0.5, 0.5]]
