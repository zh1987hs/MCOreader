import pathlib
from typing import Tuple

import fitz
from pdfminer.high_level import extract_text


def parse_pdf(path: pathlib.Path) -> Tuple[str, dict]:
    try:
        text = ""
        with fitz.open(path) as doc:
            for page in doc:
                text += page.get_text()
        if text.strip():
            return text, {"parser": "pymupdf", "pages": doc.page_count}
    except Exception:
        text = extract_text(str(path))
        return text, {"parser": "pdfminer", "pages": None}
    return "", {"parser": "none", "pages": None}
