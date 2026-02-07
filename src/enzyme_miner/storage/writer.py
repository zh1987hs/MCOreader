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

