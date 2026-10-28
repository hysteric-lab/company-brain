from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from typing import Literal, Protocol

from .config import DIM, EMBED_BATCH, MODEL, VOYAGE_EMBED

InputType = Literal["document", "query"]


class Embedder(Protocol):
    def embed(self, texts: list[str], input_type: InputType) -> list[list[float]]: ...


class VoyageEmbedder:
    def __init__(self, key: str):
        self.key = key

    def _batch(self, texts: list[str], input_type: InputType) -> list[list[float]]:
        req = urllib.request.Request(
            VOYAGE_EMBED,
            data=json.dumps({"model": MODEL, "input": texts, "input_type": input_type,
                             "output_dimension": DIM}).encode(),
            headers={"Content-Type": "application/json", "Authorization": f"Bearer {self.key}"},
        )
        for attempt in range(5):
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    return [d["embedding"] for d in json.loads(resp.read())["data"]]
            except urllib.error.HTTPError as e:
                if e.code in (429, 500, 502, 503) and attempt < 4:
                    time.sleep(2 ** attempt * 5)
                    continue
                raise
            except urllib.error.URLError:  # network blip: same back-off
                if attempt < 4:
                    time.sleep(2 ** attempt * 5)
                    continue
                raise
        raise RuntimeError("unreachable")

    def embed(self, texts: list[str], input_type: InputType) -> list[list[float]]:
        out: list[list[float]] = []
        for i in range(0, len(texts), EMBED_BATCH):
            out += self._batch(texts[i : i + EMBED_BATCH], input_type)
        return out


def default_embedder() -> Embedder | None:
    key = os.environ.get("VOYAGE_API_KEY", "").strip()
    if not key:
        print("(vector search off: VOYAGE_API_KEY not set)", file=sys.stderr)
        return None
    return VoyageEmbedder(key)
