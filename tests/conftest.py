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
