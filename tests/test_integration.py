"""Live tests against Voyage and the GitLab handbook demo corpus.

Run: bash scripts/fetch_demo_corpus.sh
     BRAIN_INTEGRATION=1 VOYAGE_API_KEY=... pytest -q -m integration
"""
import os
from pathlib import Path

import pytest

from company_brain.embed import default_embedder
from company_brain.ingest import ingest
from company_brain.search import search
from company_brain.store import connect

CORPUS = Path(__file__).resolve().parents[1] / "demo" / "corpus"

pytestmark = [
    pytest.mark.integration,
    pytest.mark.skipif(os.environ.get("BRAIN_INTEGRATION") != "1",
                       reason="set BRAIN_INTEGRATION=1 and VOYAGE_API_KEY"),
]


@pytest.fixture(scope="module")
def live(tmp_path_factory):
    if not CORPUS.is_dir():
        pytest.skip("demo corpus missing: run scripts/fetch_demo_corpus.sh")
    embedder = default_embedder()
    if embedder is None:
        pytest.skip("VOYAGE_API_KEY not set")
    con = connect(tmp_path_factory.mktemp("live") / "live.db")
    ingest(con, CORPUS, embedder)
    yield con, embedder
    con.close()


def top3_paths(live, question):
    con, embedder = live
    return [h.path for h in search(con, question, embedder, top=3)]


def test_zh_question_en_doc_leave(live):
    paths = top3_paths(live, "員工請病假的規定是什麼？")
    assert any(p.endswith("time-off-types.md") for p in paths), paths


def test_zh_question_en_doc_expenses(live):
    paths = top3_paths(live, "出差的費用可以怎麼報銷？")
    assert any(p.endswith("finance/expenses.md") for p in paths), paths


def test_en_control_values(live):
    paths = top3_paths(live, "What does iteration mean as a company value?")
    assert "values/_index.md" in paths, paths


# Held-out questions: none of these were used to calibrate MAX_VEC_DISTANCE.
@pytest.mark.parametrize("question", ["What's a good recipe for pad thai?",
                                      "量子電腦的原理是什麼？"])
def test_off_topic_empty(live, question):
    con, embedder = live
    assert search(con, question, embedder) == []


def test_heldout_on_topic_bereavement(live):
    paths = top3_paths(live, "How many days of bereavement leave do I get?")
    assert any(p.endswith("time-off-types.md") for p in paths), paths
