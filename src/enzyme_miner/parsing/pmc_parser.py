import pathlib
from typing import Tuple

from bs4 import BeautifulSoup


def parse_pmc_xml(path: pathlib.Path) -> Tuple[str, dict]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(content, "lxml-xml")
    texts = []
    for section in soup.find_all(["title", "p", "table-wrap", "fig"]):
        text = section.get_text(" ", strip=True)
        if text:
            texts.append(text)
    return "\n".join(texts), {"parser": "pmc-xml", "sections": len(texts)}
