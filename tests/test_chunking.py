from company_brain.chunking import chunk_spans, line_range


def test_chunk_spans_short():
    assert chunk_spans(10) == [(1, 10)]


def test_chunk_spans_overlap():
    assert chunk_spans(2500) == [(1, 1200), (1001, 1200), (2001, 500)]


def test_line_range():
    text = "a\nb\nc\nd"
    assert line_range(text, 3, 3) == (2, 3)
