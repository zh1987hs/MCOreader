import pathlib
from typing import Tuple


def parse_txt(path: pathlib.Path) -> Tuple[str, dict]:
    return path.read_text(encoding="utf-8", errors="ignore"), {"parser": "plain"}
