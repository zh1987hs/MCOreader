import pathlib
from typing import Iterable


DEFAULT_EXTENSIONS = {".pdf", ".docx", ".html", ".htm", ".txt"}


def scan_local_folders(paths: Iterable[pathlib.Path], extensions: Iterable[str] | None = None) -> list[pathlib.Path]:
    exts = {ext.lower() for ext in (extensions or DEFAULT_EXTENSIONS)}
    results: list[pathlib.Path] = []
    for base in paths:
        if not base.exists():
            continue
        if base.is_file():
            if base.suffix.lower() in exts:
                results.append(base)
            continue
        for path in base.rglob("*"):
            if path.is_file() and path.suffix.lower() in exts:
                results.append(path)
    return results
