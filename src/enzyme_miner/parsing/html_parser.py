import pathlib
from typing import Tuple

from bs4 import BeautifulSoup


def parse_html(path: pathlib.Path) -> Tuple[str, dict]:
    content = path.read_text(encoding="utf-8", errors="ignore")
    soup = BeautifulSoup(content, "lxml")
    for script in soup(["script", "style"]):
        script.decompose()
    text = soup.get_text(separator="\n")
    return text, {"parser": "beautifulsoup", "title": soup.title.string if soup.title else None}
