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
        buffer = []
        for idx, paragraph in enumerate(paragraphs, start=1):
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
