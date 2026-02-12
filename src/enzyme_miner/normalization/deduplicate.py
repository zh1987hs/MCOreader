from collections import defaultdict
from typing import Any


def _merge_records(records: list[dict[str, Any]]) -> dict[str, Any]:
    merged = records[0].copy()
    for record in records[1:]:
        for section in ["paper", "enzyme_entity", "assay_context", "kinetic_or_activity", "evidence", "extraction_meta"]:
            for key, value in record.get(section, {}).items():
                if merged.get(section, {}).get(key) in (None, "") and value not in (None, ""):
                    merged[section][key] = value
        if record.get("evidence", {}).get("confidence"):
            if (merged["evidence"].get("confidence") or 0) < record["evidence"]["confidence"]:
                merged["evidence"] = record["evidence"]
        warnings = set(merged["extraction_meta"].get("warnings", []))
        warnings.update(record["extraction_meta"].get("warnings", []))
        merged["extraction_meta"]["warnings"] = sorted(warnings)
    return merged


def deduplicate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for record in records:
        paper = record.get("paper", {})
        enzyme = record.get("enzyme_entity", {})
        assay = record.get("assay_context", {})
        kinetic = record.get("kinetic_or_activity", {})
        key = "|".join(
            [
                str(paper.get("doi") or paper.get("paper_id") or ""),
                str(enzyme.get("enzyme_name") or enzyme.get("gene_name") or ""),
                str(assay.get("substrate_name_normalized") or assay.get("substrate_name_raw") or ""),
                str(kinetic.get("parameter_type") or ""),
                str(assay.get("pH") or ""),
                str(assay.get("temperature_c") or ""),
                str(assay.get("buffer") or ""),
            ]
        )
        grouped[key].append(record)

    return [_merge_records(group) for group in grouped.values()]
