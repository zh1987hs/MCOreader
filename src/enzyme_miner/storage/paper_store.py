from dataclasses import dataclass


@dataclass
class PaperMetadata:
    paper_id: str | None
    doi: str | None
    title: str | None
    journal: str | None
    year: int | None
    url: str | None
    open_access: bool | None
    fulltext_source: str | None
    abstract: str | None = None
    file_path: str | None = None
    pmcid: str | None = None
