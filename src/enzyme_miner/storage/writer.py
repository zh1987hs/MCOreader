import csv
import json
import pathlib
from typing import Any

from enzyme_miner.storage.paper_store import PaperMetadata
from enzyme_miner.storage.sqlite_writer import write_sqlite


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
        writer = csv.DictWriter(handle, fieldnames=_flatten_keys(records[0]))
        writer.writeheader()
        for record in records:
            writer.writerow(_flatten_record(record))

    write_sqlite(output_dir / "records.sqlite", records)


def _flatten_keys(record: dict[str, Any]) -> list[str]:
    keys = []
    for section, values in record.items():
        if isinstance(values, dict):
            for key in values.keys():
                keys.append(f"{section}.{key}")
        else:
            keys.append(section)
    return keys


def _flatten_record(record: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for section, values in record.items():
        if isinstance(values, dict):
            for key, value in values.items():
                flattened[f"{section}.{key}"] = value
        else:
            flattened[section] = values
    return flattened
