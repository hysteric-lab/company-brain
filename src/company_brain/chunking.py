from .config import CHUNK_OVERLAP, CHUNK_SIZE


def chunk_spans(n: int) -> list[tuple[int, int]]:
    """Offsets (start, length) covering n chars with overlap. start is 1-based."""
    if n <= CHUNK_SIZE:
        return [(1, n)]
    spans, pos = [], 0
    step = CHUNK_SIZE - CHUNK_OVERLAP
    while pos < n:
        spans.append((pos + 1, min(CHUNK_SIZE, n - pos)))
        if pos + CHUNK_SIZE >= n:
            break
        pos += step
    return spans


def line_range(text: str, start: int, length: int) -> tuple[int, int]:
    """1-based first and last line covered by text[start-1 : start-1+length]."""
    first = text.count("\n", 0, start - 1) + 1
    last = first + text.count("\n", start - 1, max(start - 1, start - 1 + length - 1))
    return first, last
