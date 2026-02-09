import pathlib
import logging
from typing import Tuple

import fitz
from pdfminer.high_level import extract_text


LOGGER = logging.getLogger(__name__)


def parse_pdf(path: pathlib.Path) -> Tuple[str, dict]:
    try:
        text = ""
        with fitz.open(path) as doc:
            page_count = doc.page_count
            for page in doc:
                text += page.get_text()
        if text.strip():
            return text, {"parser": "pymupdf", "pages": page_count}
    except Exception as exc:
        LOGGER.warning("PyMuPDF failed to parse %s: %s", path, exc)
    try:
        text = extract_text(str(path))
        if text.strip():
            return text, {"parser": "pdfminer", "pages": None}
    except Exception as exc:
        LOGGER.warning("pdfminer failed to parse %s: %s", path, exc)
    return "", {"parser": "none", "pages": None}
