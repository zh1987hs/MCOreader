import re

from enzyme_miner.chunking.chunker import Chunk
from enzyme_miner.normalization.substrate import DEFAULT_SUBSTRATE_DICT


BASE_KEYWORDS = [
    "km",
    "kcat",
    "kcat/km",
    "kcat / km",
    "kcat/ km",
    "turnover number",
    "turnover",
    "vmax",
    "specific activity",
    "relative activity",
    "activity toward",
    "substrate specificity",
    "substrate",
    "oxidation",
    "oxidizes",
    "oxidized",
    "dye decolorization",
    "decolorization",
    "ferroxidase",
    "bilirubin oxidase",
    "manganese",
    "ferrous",
]


def _build_keywords() -> list[str]:
    keywords = set(BASE_KEYWORDS)
    for normalized, entry in DEFAULT_SUBSTRATE_DICT.items():
        keywords.add(normalized.lower())
        for synonym in entry.get("synonyms", []):
            keywords.add(str(synonym).lower())
    return sorted(keywords)


KEYWORDS = _build_keywords()
PATTERN = re.compile("|".join(re.escape(k) for k in KEYWORDS if k), re.IGNORECASE)


def find_candidates(chunks: list[Chunk]) -> list[Chunk]:
    return [chunk for chunk in chunks if PATTERN.search(chunk.text)]
