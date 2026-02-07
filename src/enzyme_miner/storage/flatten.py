from typing import Any


def flatten_keys(record: dict[str, Any]) -> list[str]:
    keys = []
    for section, values in record.items():
        if isinstance(values, dict):
            for key in values.keys():
                keys.append(f"{section}.{key}")
        else:
            keys.append(section)
    return keys


def flatten_record(record: dict[str, Any]) -> dict[str, Any]:
    flattened: dict[str, Any] = {}
    for section, values in record.items():
        if isinstance(values, dict):
            for key, value in values.items():
                flattened[f"{section}.{key}"] = value
        else:
            flattened[section] = values
    return flattened
