import json
import pathlib
from dataclasses import dataclass
from typing import Any


DEFAULT_SUBSTRATE_DICT = {
    "Mn(II)": {"synonyms": ["Mn2+", "manganese(II)", "Mn(II)", "Mn(2+)", "Mn II"], "category": "metal"},
    "Fe(II)": {"synonyms": ["Fe2+", "ferrous iron", "Fe(II)", "Fe II"], "category": "metal"},
    "ABTS": {"synonyms": ["ABTS", "2,2'-azino-bis(3-ethylbenzothiazoline-6-sulfonic acid)"], "category": "dye"},
    "syringaldazine": {"synonyms": ["syringaldazine", "SGZ"], "category": "phenolic"},
    "2,6-DMP": {"synonyms": ["2,6-DMP", "2,6-dimethoxyphenol"], "category": "phenolic"},
    "guaiacol": {"synonyms": ["guaiacol"], "category": "phenolic"},
    "catechol": {"synonyms": ["catechol"], "category": "phenolic"},
    "bilirubin": {"synonyms": ["bilirubin"], "category": "tetrapyrrole"},
    "p-phenylenediamine": {"synonyms": ["p-phenylenediamine", "PPD"], "category": "amine"},
}


@dataclass
class NormalizedSubstrate:
    raw: str
    normalized: str
    category: str | None
    warnings: list[str]


def load_substrate_dictionary(path: str | None) -> dict[str, Any]:
    if not path:
        return DEFAULT_SUBSTRATE_DICT
    file_path = pathlib.Path(path)
    if not file_path.exists():
        return DEFAULT_SUBSTRATE_DICT
    if file_path.suffix.lower() in {".yaml", ".yml"}:
        import yaml

        return yaml.safe_load(file_path.read_text())
    if file_path.suffix.lower() == ".json":
        return json.loads(file_path.read_text())
    return DEFAULT_SUBSTRATE_DICT


def normalize_substrate(name_raw: str | None, substrate_dict: dict[str, Any]) -> NormalizedSubstrate:
    if not name_raw:
        return NormalizedSubstrate(raw="", normalized="", category=None, warnings=["substrate_missing"])
    lowered = name_raw.lower()
    for normalized, entry in substrate_dict.items():
        synonyms = [normalized] + entry.get("synonyms", [])
        if any(lowered == syn.lower() for syn in synonyms):
            return NormalizedSubstrate(
                raw=name_raw,
                normalized=normalized,
                category=entry.get("category"),
                warnings=[],
            )
    return NormalizedSubstrate(
        raw=name_raw,
        normalized=name_raw,
        category=None,
        warnings=["substrate_unmapped"],
    )
