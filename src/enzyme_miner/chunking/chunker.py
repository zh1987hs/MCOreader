from dataclasses import dataclass

from enzyme_miner.parsing.loader import Document


@dataclass
class Chunk:
    document_path: str
    text: str
    location_hint: str | None


def chunk_documents(documents: list[Document], max_length: int = 1200) -> list[Chunk]:
    chunks: list[Chunk] = []
    for doc in documents:
        paragraphs = [p.strip() for p in doc.text.split("\n") if p.strip()]
        special_indices = _find_table_figure_indices(paragraphs)
        used_indices: set[int] = set()
        for idx in sorted(special_indices):
            start = max(0, idx - 1)
            end = min(len(paragraphs), idx + 2)
            window = paragraphs[start:end]
            used_indices.update(range(start, end))
            text = "\n".join(window)
            if text:
                chunks.append(
                    Chunk(
                        document_path=str(doc.path),
                        text=text,
                        location_hint=f"paragraph {start + 1}-{end}",
                    )
                )
        buffer = []
        for idx, paragraph in enumerate(paragraphs, start=1):
            if (idx - 1) in used_indices:
                continue
            if sum(len(p) for p in buffer) + len(paragraph) > max_length and buffer:
                text = "\n".join(buffer)
                chunks.append(
                    Chunk(
                        document_path=str(doc.path),
                        text=text,
                        location_hint=f"paragraph {idx - len(buffer)}-{idx - 1}",
                    )
                )
                buffer = []
            buffer.append(paragraph)
        if buffer:
            text = "\n".join(buffer)
            start = max(1, len(paragraphs) - len(buffer) + 1)
            chunks.append(
                Chunk(
                    document_path=str(doc.path),
                    text=text,
                    location_hint=f"paragraph {start}-{len(paragraphs)}",
                )
            )
    return chunks


def _find_table_figure_indices(paragraphs: list[str]) -> set[int]:
    indices: set[int] = set()
    for idx, paragraph in enumerate(paragraphs):
        lowered = paragraph.lower()
        if "table" in lowered or "fig." in lowered or "figure" in lowered:
            indices.add(idx)
    return indices
