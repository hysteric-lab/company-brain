from pathlib import Path

import pytest

from company_brain.store import connect


@pytest.fixture
def con(tmp_path: Path):
    c = connect(tmp_path / "brain.db")
    yield c
    c.close()


@pytest.fixture
def corpus(tmp_path: Path) -> Path:
    root = tmp_path / "docs"
    (root / "sub").mkdir(parents=True)
    (root / "a.md").write_text("first line\nsecond old phrase here\nthird line\n", encoding="utf-8")
    (root / "sub" / "b.txt").write_text("plain text file\n", encoding="utf-8")
    (root / "c.pdf").write_bytes(b"%PDF-1.4 not ingested")
    return root


class FakeEmbedder:
    """Deterministic bag-of-words embedder: crc32 buckets, L2-normalised.
    Texts sharing words are close; disjoint texts sit at distance ~sqrt(2)."""

    def __init__(self):
        self.calls = 0

    def embed(self, texts, input_type):
        import math
        import re
        import zlib

        from company_brain.config import DIM

        self.calls += 1
        out = []
        for t in texts:
            v = [0.0] * DIM
            for w in re.findall(r"\w+", t.lower()):
                v[zlib.crc32(w.encode()) % DIM] += 1.0
            n = math.sqrt(sum(x * x for x in v)) or 1.0
            out.append([x / n for x in v])
        return out


@pytest.fixture
def fake_embedder():
    return FakeEmbedder()
