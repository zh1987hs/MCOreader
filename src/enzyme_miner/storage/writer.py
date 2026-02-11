import csv
import json
import pathlib
from typing import Any

from enzyme_miner.storage.paper_store import PaperMetadata
from enzyme_miner.storage.sqlite_writer import write_sqlite
from enzyme_miner.storage.flatten import flatten_keys, flatten_record


def write_outputs(output_dir: pathlib.Path, papers: list[PaperMetadata], records: list[dict[str, Any]]) -> None:
    papers_path = output_dir / "papers.csv"
    records_path = output_dir / "records.jsonl"
    csv_records_path = output_dir / "records.csv"
    missing_path = output_dir / "missing_fulltext.xlsx"
    missing_csv_path = output_dir / "missing_fulltext.csv"

    with papers_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "paper_id",
                "doi",
                "title",
                "journal",
                "year",
                "url",
                "open_access",
                "fulltext_source",
                "abstract",
                "file_path",
                "pmcid",
            ],
        )
        writer.writeheader()
        for paper in papers:
            writer.writerow(paper.__dict__)

    _write_missing_fulltext_excel(missing_path, missing_csv_path, papers)

    with records_path.open("w", encoding="utf-8") as handle:
        for record in records:
            handle.write(json.dumps(record, ensure_ascii=False))
            handle.write("\n")

    with csv_records_path.open("w", newline="", encoding="utf-8") as handle:
        if not records:
            return
        writer = csv.DictWriter(handle, fieldnames=flatten_keys(records[0]))
        writer.writeheader()
        for record in records:
            writer.writerow(flatten_record(record))

    write_sqlite(output_dir / "records.sqlite", records)


def _write_missing_fulltext_excel(
    path: pathlib.Path,
    fallback_csv_path: pathlib.Path,
    papers: list[PaperMetadata],
) -> None:
    rows = [
        ["title", "journal", "doi", "year", "url"],
    ]
    for paper in papers:
        if paper.file_path:
            continue
        if not (paper.title or paper.doi):
            continue
        rows.append([paper.title, paper.journal, paper.doi, paper.year, paper.url])
    try:
        from openpyxl import Workbook

        workbook = Workbook()
        sheet = workbook.active
        sheet.title = "missing_fulltext"
        for row in rows:
            sheet.append(row)
        workbook.save(path)
    except ModuleNotFoundError:
        with fallback_csv_path.open("w", newline="", encoding="utf-8") as handle:
            writer = csv.writer(handle)
            writer.writerows(rows)
