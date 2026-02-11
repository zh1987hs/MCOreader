import pathlib
from collections import Counter
from typing import Any

from enzyme_miner.storage.paper_store import PaperMetadata


def build_report(output_dir: pathlib.Path, papers: list[PaperMetadata], records: list[dict[str, Any]]) -> pathlib.Path:
    substrates = Counter()
    params = Counter()
    needs_review = [r for r in records if r["extraction_meta"].get("needs_human_review")]

    for record in records:
        substrate = record["assay_context"].get("substrate_name_normalized")
        parameter = record["kinetic_or_activity"].get("parameter_type")
        if substrate:
            substrates[substrate] += 1
        if parameter:
            params[parameter] += 1

    report_lines = [
        "# Enzyme Miner Report",
        "",
        f"Total papers: {len(papers)}",
        f"Total records: {len(records)}",
        "",
        "## Substrate spectrum (top)\n",
    ]

    for substrate, count in substrates.most_common(20):
        report_lines.append(f"- {substrate}: {count}")

    report_lines.extend(["", "## Parameter distribution\n"])
    for param, count in params.most_common():
        report_lines.append(f"- {param}: {count}")

    report_lines.extend(["", "## Needs human review\n"])
    for record in needs_review[:20]:
        evidence = record["evidence"].get("evidence_text", "")
        report_lines.append(f"- {record['assay_context'].get('substrate_name_raw')}: {evidence[:120]}...")

    report_path = output_dir / "report.md"
    report_path.write_text("\n".join(report_lines), encoding="utf-8")
    return report_path
