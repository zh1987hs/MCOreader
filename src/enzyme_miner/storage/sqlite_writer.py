import json
import pathlib
import sqlite3
from typing import Any

from enzyme_miner.storage.flatten import flatten_record


def write_sqlite(db_path: pathlib.Path, records: list[dict[str, Any]]) -> None:
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                record_json TEXT NOT NULL
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS records_flat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data_json TEXT NOT NULL
            )
            """
        )
        for record in records:
            conn.execute("INSERT INTO records (record_json) VALUES (?)", (json.dumps(record, ensure_ascii=False),))
            conn.execute("INSERT INTO records_flat (data_json) VALUES (?)", (json.dumps(flatten_record(record), ensure_ascii=False),))
        conn.commit()
    finally:
        conn.close()
