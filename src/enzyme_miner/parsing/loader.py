import pathlib
from dataclasses import dataclass

from enzyme_miner.parsing.pdf_parser import parse_pdf
from enzyme_miner.parsing.docx_parser import parse_docx
from enzyme_miner.parsing.html_parser import parse_html
from enzyme_miner.parsing.txt_parser import parse_txt
from enzyme_miner.parsing.pmc_parser import parse_pmc_xml


@dataclass
class Document:
    path: pathlib.Path
    text: str
    metadata: dict


def load_documents(paths: list[pathlib.Path]) -> list[Document]:
    documents: list[Document] = []
    for root in paths:
        if not root.exists():
            continue
        candidates = [root] if root.is_file() else list(root.rglob("*"))
        for path in candidates:
            if path.is_dir():
                continue
            suffix = path.suffix.lower()
            if suffix == ".pdf":
                text, meta = parse_pdf(path)
            elif suffix == ".docx":
                text, meta = parse_docx(path)
            elif suffix in {".html", ".htm"}:
                text, meta = parse_html(path)
            elif suffix == ".txt":
                text, meta = parse_txt(path)
            elif suffix == ".xml":
                text, meta = parse_pmc_xml(path)
            else:
                continue
            documents.append(Document(path=path, text=text, metadata=meta))
    return documents
