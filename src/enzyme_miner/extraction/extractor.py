import json
import pathlib
import re
from datetime import datetime
from typing import Any

from jsonschema import ValidationError, validate

from enzyme_miner.chunking.chunker import Chunk
from enzyme_miner.extraction.llm_client import LLMConfig, call_llm
from enzyme_miner.extraction.schema import RECORD_SCHEMA
from enzyme_miner.normalization.substrate import load_substrate_dictionary, normalize_substrate
from enzyme_miner.normalization.units import normalize_value

PARAM_PATTERN = re.compile(
    r"(?P<param>kcat\/km|kcat\/km|kcat|km|vmax|specific activity|relative activity|rate)"
    r"\s*[:=]?\s*(?P<value>[0-9]+(?:\.[0-9]+)?)\s*(?P<unit>[A-Za-zµ/\-\^0-9]+)",
    re.IGNORECASE,
)
SUBSTRATE_PATTERN = re.compile(r"\b(ABTS|2,6-DMP|SGZ|syringaldazine|guaiacol|catechol|bilirubin|Mn\(II\)|Fe\(II\)|PPD)\b", re.IGNORECASE)
QUALITATIVE_PATTERN = re.compile(r"oxidize|oxidation|activity|active toward", re.IGNORECASE)


def _base_record() -> dict[str, Any]:
    return {
        "paper": {
            "paper_id": None,
            "doi": None,
            "title": None,
            "journal": None,
            "year": None,
            "url": None,
            "open_access": None,
            "fulltext_source": None,
        },
        "enzyme_entity": {
            "enzyme_name": None,
            "gene_name": None,
            "organism": None,
            "ec_number": None,
            "expression_system": None,
            "purification_level": None,
            "sequence_accession": None,
        },
        "assay_context": {
            "assay_type": None,
            "substrate_name_raw": None,
            "substrate_name_normalized": None,
            "substrate_category": None,
            "mediator_or_coupler": None,
            "pH": None,
            "temperature_c": None,
            "buffer": None,
            "cofactors": None,
            "detection_method": None,
        },
        "kinetic_or_activity": {
            "parameter_type": None,
            "value": None,
            "unit_raw": None,
            "unit_normalized": None,
            "value_normalized": None,
            "error": None,
            "notes": None,
        },
        "evidence": {
            "evidence_text": "",
            "location_hint": None,
            "confidence": None,
        },
        "extraction_meta": {
            "extracted_by": "heuristic",
            "timestamp": datetime.utcnow().isoformat(),
            "warnings": [],
            "needs_human_review": False,
        },
    }


def extract_records(
    chunks: list[Chunk],
    config: dict[str, Any],
    paper_lookup: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    substrate_dict = load_substrate_dictionary(config.get("substrate_dictionary"))
    records: list[dict[str, Any]] = []
    use_llm = bool(config.get("enable", False))

    if use_llm:
        llm_config = LLMConfig(
            provider=config.get("provider", "openai"),
            model=config.get("model", "gpt-4o-mini"),
            temperature=float(config.get("temperature", 0)),
            max_tokens=int(config.get("max_tokens", 1200)),
            api_key=config.get("api_key"),
            api_base=config.get("api_base"),
            api_key_header=config.get("api_key_header", "Authorization"),
            api_key_prefix=config.get("api_key_prefix", "Bearer"),
            response_json_path=config.get("response_json_path"),
            response_format=config.get("response_format"),
        )
        prompt_template = pathlib.Path(
            config.get("extract_prompt_path", "src/enzyme_miner/extraction/prompts/extract_prompt.txt")
        ).read_text(encoding="utf-8")
        repair_template = pathlib.Path(
            config.get("repair_prompt_path", "src/enzyme_miner/extraction/prompts/repair_prompt.txt")
        ).read_text(encoding="utf-8")
        for chunk in chunks:
            prompt_input = _build_prompt_input(chunk, substrate_dict, config, paper_lookup)
            prompt = prompt_template.replace("-----BEGIN_EXTRACT_PROMPT-----\n", "").replace(
                "\n-----END_EXTRACT_PROMPT-----", ""
            )
            prompt = f"{prompt}\n\nINPUT_JSON:\n{json.dumps(prompt_input, ensure_ascii=False)}"
            raw = call_llm(prompt, llm_config)
            parsed = _parse_llm_output(raw, repair_template, llm_config)
            for record in parsed:
                validate(instance=record, schema=RECORD_SCHEMA)
                records.append(record)
        return records

    for chunk in chunks:
        matches = list(PARAM_PATTERN.finditer(chunk.text))
        substrates = [m.group(0) for m in SUBSTRATE_PATTERN.finditer(chunk.text)]
        if matches:
            for match in matches:
                param_raw = match.group("param").lower()
                parameter_type = {
                    "kcat": "kcat",
                    "km": "Km",
                    "kcat/km": "kcat_over_Km",
                    "vmax": "Vmax",
                    "specific activity": "specific_activity",
                    "relative activity": "relative_activity",
                    "rate": "rate",
                }.get(param_raw, "rate")
                value = float(match.group("value"))
                unit_raw = match.group("unit")
                substrate_raw = substrates[0] if substrates else None
                normalized_substrate = normalize_substrate(substrate_raw, substrate_dict)
                normalized_value = normalize_value(parameter_type, value, unit_raw)

                record = _base_record()
                record["assay_context"]["substrate_name_raw"] = substrate_raw
                record["assay_context"]["substrate_name_normalized"] = normalized_substrate.normalized
                record["assay_context"]["substrate_category"] = normalized_substrate.category
                record["kinetic_or_activity"]["parameter_type"] = parameter_type
                record["kinetic_or_activity"]["value"] = value
                record["kinetic_or_activity"]["unit_raw"] = unit_raw
                record["kinetic_or_activity"]["value_normalized"] = normalized_value.value
                record["kinetic_or_activity"]["unit_normalized"] = normalized_value.unit_normalized
                record["evidence"]["evidence_text"] = chunk.text[:300]
                record["evidence"]["location_hint"] = chunk.location_hint
                record["evidence"]["confidence"] = 0.7
                warnings = normalized_substrate.warnings + normalized_value.warnings
                record["extraction_meta"]["warnings"] = warnings
                record["extraction_meta"]["needs_human_review"] = bool(warnings)
                validate(instance=record, schema=RECORD_SCHEMA)
                records.append(record)
        elif QUALITATIVE_PATTERN.search(chunk.text) and substrates:
            for substrate_raw in substrates:
                normalized_substrate = normalize_substrate(substrate_raw, substrate_dict)
                record = _base_record()
                record["assay_context"]["substrate_name_raw"] = substrate_raw
                record["assay_context"]["substrate_name_normalized"] = normalized_substrate.normalized
                record["assay_context"]["substrate_category"] = normalized_substrate.category
                record["kinetic_or_activity"]["parameter_type"] = "qualitative"
                record["kinetic_or_activity"]["notes"] = "qualitative only"
                record["evidence"]["evidence_text"] = chunk.text[:300]
                record["evidence"]["location_hint"] = chunk.location_hint
                record["evidence"]["confidence"] = 0.4
                warnings = normalized_substrate.warnings
                record["extraction_meta"]["warnings"] = warnings
                record["extraction_meta"]["needs_human_review"] = bool(warnings)
                validate(instance=record, schema=RECORD_SCHEMA)
                records.append(record)
    return records


def _build_prompt_input(
    chunk: Chunk,
    substrate_dict: dict[str, Any],
    config: dict[str, Any],
    paper_lookup: dict[str, Any] | None,
) -> dict[str, Any]:
    paper_meta = {}
    if paper_lookup and chunk.document_path in paper_lookup:
        paper = paper_lookup[chunk.document_path]
        paper_meta = {
            "doi": paper.doi,
            "title": paper.title,
            "journal": paper.journal,
            "year": paper.year,
        }
    return {
        "paper": paper_meta,
        "enzyme_hint": {
            "enzyme_family": config.get("enzyme_family"),
            "gene_names_possible": config.get("gene_names_possible", []),
            "enzyme_names_possible": config.get("enzyme_names_possible", []),
        },
        "chunk": chunk.text,
        "location_hint": chunk.location_hint,
        "substrate_dictionary": substrate_dict,
        "unit_policy": config.get("unit_policy", {}),
    }


def _parse_llm_output(raw: str, repair_template: str, llm_config: LLMConfig) -> list[dict[str, Any]]:
    data = _safe_json_load(raw, llm_config)
    if data is None:
        payload = {
            "bad_json": raw,
            "schema_hint": RECORD_SCHEMA,
        }
        prompt = repair_template.replace("-----BEGIN_REPAIR_PROMPT-----\n", "").replace(
            "\n-----END_REPAIR_PROMPT-----", ""
        )
        prompt = f"{prompt}\n\nINPUT_JSON:\n{json.dumps(payload, ensure_ascii=False)}"
        repaired = call_llm(prompt, llm_config)
        data = _safe_json_load(repaired, llm_config)
        if data is None:
            raise ValidationError("LLM output could not be parsed as JSON after repair")
    records = data.get("records", []) if isinstance(data, dict) else []
    if not isinstance(records, list):
        raise ValidationError("records must be a list")
    return records


def _safe_json_load(text: str, llm_config: LLMConfig) -> dict[str, Any] | None:
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        cleaned = _extract_json_from_text(text)
        if cleaned:
            try:
                return json.loads(cleaned)
            except json.JSONDecodeError:
                return None
    return None


def _extract_json_from_text(text: str) -> str | None:
    start = text.find("{")
    end = text.rfind("}")
    if start == -1 or end == -1 or end <= start:
        return None
    return text[start : end + 1]


def save_prompt_inputs(path: str, payload: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, ensure_ascii=False, indent=2))
