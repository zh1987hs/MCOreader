import re

from enzyme_miner.chunking.chunker import Chunk

KEYWORDS = [
    "km",
    "kcat",
    "kcat/km",
    "kcat / km",
    "kcat/km",
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
    "abts",
    "2,6-dmp",
    "syringaldazine",
    "guaiacol",
    "catechol",
    "l-dopa",
    "l dopa",
    "p-phenylenediamine",
    "o-phenylenediamine",
    "ppd",
    "opd",
    "vanillin",
    "syringic acid",
    "bilirubin",
    "ferroxidase",
    "bilirubin oxidase",
    "mn(II)",
    "fe(II)",
    "fe(III)",
    "manganese",
    "ferrous",
]

PATTERN = re.compile("|".join(re.escape(k) for k in KEYWORDS), re.IGNORECASE)


def find_candidates(chunks: list[Chunk]) -> list[Chunk]:
    return [chunk for chunk in chunks if PATTERN.search(chunk.text)]
