from pathlib import Path

import pytest

from company_brain.store import connect


@pytest.fixture
def con(tmp_path: Path):
    c = connect(tmp_path / "brain.db")
    yield c
    c.close()


# Each file stays under 15 words in total: the bag-of-words FakeEmbedder's
# distances grow with document length, and the unit tests pin max_distance=1.2.
DOCS = {
    "leave.md": "# Leave\nSick leave policy: tell your manager.\n",
    "expenses.md": "# Expenses\nTravel costs are reimbursed\nwith receipts.\n",
    "values.md": "# Values\nWe iterate in small steps.\n",
}


@pytest.fixture
def kb(tmp_path: Path):
    root = tmp_path / "kb"
    root.mkdir()
    for name, text in DOCS.items():
        (root / name).write_text(text, encoding="utf-8")
    return root


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
