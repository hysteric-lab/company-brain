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
# L2 distance on unit vectors: d = sqrt(2 - 2*cos). Calibrated in Task 5.
MAX_VEC_DISTANCE = 1.0
SUFFIXES = (".md", ".txt")
