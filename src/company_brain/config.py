"""Constants shared across the package. Values match the retrieval stack this
was extracted from (youtube archive: search.py / embed_chunks.py)."""

VOYAGE_EMBED = "https://api.voyageai.com/v1/embeddings"
MODEL = "voyage-3.5-lite"
DIM = 1024
CHUNK_SIZE = 1200
CHUNK_OVERLAP = 200
EMBED_BATCH = 64
RRF_K = 60
CANDIDATES = 50
# L2 distance on unit vectors: d = sqrt(2 - 2*cos). Vector hits farther than
# this are dropped, so an off-topic question returns nothing instead of noise.
# Calibrated 2026-10-28 on the demo corpus (scripts/fetch_demo_corpus.sh),
# nearest-chunk distance per query with voyage-3.5-lite:
#   on-topic : 0.9069 en values, 0.9145 zh parental leave, 0.9245 en taxi expense,
#              0.9269 zh sick leave, 1.0101 zh travel expenses
#   off-topic: 1.0495 en car tyre, 1.0705 en sourdough, 1.0851 zh cat purring,
#              1.1173 en capital of Peru, 1.1206 zh sushi rice, 1.1695 en 1998 World Cup
# A first cut at 1.065 (from 5 probes) let the car-tyre question through on a
# held-out test; 1.03 is the midpoint of the gap across all 11 probes. The gap
# is ~0.04 wide, so "no answer" is best-effort: recalibrate on your own corpus,
# and the MCP tool also tells Claude to judge relevance itself.
MAX_VEC_DISTANCE = 1.03
SUFFIXES = (".md", ".txt")
