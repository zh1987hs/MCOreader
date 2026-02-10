import re

from enzyme_miner.chunking.chunker import Chunk

KEYWORDS = [
    "km",
    "kcat",
    "vmax",
    "specific activity",
    "relative activity",
    "substrate",
    "oxidation",
    "abts",
    "2,6-dmp",
    "syringaldazine",
    "guaiacol",
    "catechol",
    "bilirubin",
    "ferroxidase",
    "mn(II)",
]

PATTERN = re.compile("|".join(re.escape(k) for k in KEYWORDS), re.IGNORECASE)


def find_candidates(chunks: list[Chunk]) -> list[Chunk]:
    return [chunk for chunk in chunks if PATTERN.search(chunk.text)]
