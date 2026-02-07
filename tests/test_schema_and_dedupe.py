import pathlib
import sys
import unittest
from datetime import datetime

sys.path.append(str(pathlib.Path(__file__).resolve().parents[1] / "src"))

from jsonschema import validate

from enzyme_miner.extraction.schema import RECORD_SCHEMA
from enzyme_miner.normalization.deduplicate import deduplicate_records


def build_record(substrate: str, param: str) -> dict:
    return {
        "paper": {
            "paper_id": "paper-1",
            "doi": "10.1000/demo",
            "title": "Demo",
            "journal": "Journal",
            "year": 2024,
            "url": "https://example.com",
            "open_access": True,
            "fulltext_source": "local",
        },
        "enzyme_entity": {
            "enzyme_name": "MCO",
            "gene_name": None,
            "organism": "Testus organism",
            "ec_number": None,
            "expression_system": None,
            "purification_level": "purified",
            "sequence_accession": None,
        },
        "assay_context": {
            "assay_type": "spectrophotometric",
            "substrate_name_raw": substrate,
            "substrate_name_normalized": substrate,
            "substrate_category": "dye",
            "mediator_or_coupler": None,
            "pH": 5.0,
            "temperature_c": 25.0,
            "buffer": "acetate",
            "cofactors": None,
            "detection_method": None,
        },
        "kinetic_or_activity": {
            "parameter_type": param,
            "value": 1.0,
            "unit_raw": "s^-1",
            "unit_normalized": "s^-1",
            "value_normalized": 1.0,
            "error": None,
            "notes": None,
        },
        "evidence": {
            "evidence_text": "kcat 1 s^-1 for ABTS",
            "location_hint": "Table 1",
            "confidence": 0.9,
        },
        "extraction_meta": {
            "extracted_by": "unit-test",
            "timestamp": datetime.utcnow().isoformat(),
            "warnings": [],
            "needs_human_review": False,
        },
    }


class TestSchemaAndDedup(unittest.TestCase):
    def test_schema_validation(self):
        record = build_record("ABTS", "kcat")
        validate(instance=record, schema=RECORD_SCHEMA)

    def test_deduplication(self):
        record1 = build_record("ABTS", "kcat")
        record2 = build_record("ABTS", "kcat")
        record2["evidence"]["confidence"] = 0.5
        deduped = deduplicate_records([record1, record2])
        self.assertEqual(len(deduped), 1)
        self.assertEqual(deduped[0]["evidence"]["confidence"], 0.9)


if __name__ == "__main__":
    unittest.main()
