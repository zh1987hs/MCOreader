import json
import pathlib
import re
from dataclasses import dataclass
from typing import Any


DEFAULT_SUBSTRATE_DICT = {
    "Mn(II)": {
        "synonyms": ["Mn2+", "manganese(II)", "Mn(II)", "Mn(2+)", "Mn II", "manganese ion"],
        "category": "metal",
    },
    "Fe(II)": {
        "synonyms": ["Fe2+", "ferrous iron", "Fe(II)", "Fe II", "ferrous ion"],
        "category": "metal",
    },
    "Fe(III)": {"synonyms": ["Fe3+", "ferric iron", "Fe(III)", "Fe III", "ferric ion"], "category": "metal"},
    "ABTS": {"synonyms": ["ABTS", "2,2'-azino-bis(3-ethylbenzothiazoline-6-sulfonic acid)"], "category": "dye"},
    "syringaldazine": {"synonyms": ["syringaldazine", "SGZ"], "category": "phenolic"},
    "2,6-DMP": {"synonyms": ["2,6-DMP", "2,6-dimethoxyphenol"], "category": "phenolic"},
    "guaiacol": {"synonyms": ["guaiacol"], "category": "phenolic"},
    "catechol": {"synonyms": ["catechol"], "category": "phenolic"},
    "syringic acid": {"synonyms": ["syringic acid"], "category": "phenolic"},
    "vanillin": {"synonyms": ["vanillin"], "category": "phenolic"},
    "2,2'-azino-bis(3-ethylbenzothiazoline-6-sulfonic acid)": {
        "synonyms": ["2,2'-azino-bis(3-ethylbenzothiazoline-6-sulfonic acid)", "ABTS"],
        "category": "dye",
    },
    "bilirubin": {"synonyms": ["bilirubin"], "category": "tetrapyrrole"},
    "p-phenylenediamine": {"synonyms": ["p-phenylenediamine", "PPD"], "category": "amine"},
    "o-phenylenediamine": {"synonyms": ["o-phenylenediamine", "OPD"], "category": "amine"},
    "l-DOPA": {"synonyms": ["L-DOPA", "3,4-dihydroxy-L-phenylalanine"], "category": "phenolic"},
    "lignin": {"synonyms": ["lignin"], "category": "polymer"},
    "humic acid": {"synonyms": ["humic acid"], "category": "polymer"},
    "phenol": {"synonyms": ["phenol"], "category": "phenolic"},
    "cresol": {"synonyms": ["cresol", "p-cresol", "o-cresol", "m-cresol"], "category": "phenolic"},
    "hydroquinone": {"synonyms": ["hydroquinone"], "category": "phenolic"},
    "gallic acid": {"synonyms": ["gallic acid"], "category": "phenolic"},
    "pyrogallol": {"synonyms": ["pyrogallol"], "category": "phenolic"},
    "2,4-dichlorophenol": {"synonyms": ["2,4-dichlorophenol", "2,4-DCP"], "category": "phenolic"},
    "indigo carmine": {"synonyms": ["indigo carmine", "indigocarmine"], "category": "dye"},
    "methylene blue": {"synonyms": ["methylene blue"], "category": "dye"},
    "rhodamine B": {"synonyms": ["rhodamine B", "rhodamine-B"], "category": "dye"},
    "Reactive Blue 19": {"synonyms": ["Reactive Blue 19", "RB19"], "category": "dye"},
    "Reactive Black 5": {"synonyms": ["Reactive Black 5", "RB5"], "category": "dye"},
    "methyl orange": {"synonyms": ["methyl orange"], "category": "dye"},
    "malachite green": {"synonyms": ["malachite green"], "category": "dye"},
    "Cr(III)": {"synonyms": ["Cr3+", "chromium(III)", "Cr(III)"], "category": "metal"},
    "Cu(II)": {"synonyms": ["Cu2+", "copper(II)", "Cu(II)", "Cu II"], "category": "metal"},
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
    lowered = name_raw.lower().strip()
    for normalized, entry in substrate_dict.items():
        synonyms = [normalized] + entry.get("synonyms", [])
        if any(_matches_synonym(lowered, syn) for syn in synonyms):
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


def _matches_synonym(value: str, synonym: str) -> bool:
    candidate = synonym.lower().strip()
    if not candidate:
        return False
    if value == candidate:
        return True
    pattern = r"\b" + re.escape(candidate) + r"\b"
    return re.search(pattern, value) is not None
