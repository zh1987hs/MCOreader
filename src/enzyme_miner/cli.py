import json
import logging
import pathlib
from datetime import datetime

import yaml

from enzyme_miner.ingestion.online import OnlineRetriever
from enzyme_miner.parsing.loader import load_documents
from enzyme_miner.chunking.chunker import chunk_documents
from enzyme_miner.candidate_finder.candidates import find_candidates
from enzyme_miner.extraction.extractor import extract_records
from enzyme_miner.normalization.deduplicate import deduplicate_records
from enzyme_miner.storage.writer import write_outputs
from enzyme_miner.reporting.report import build_report


LOGGER = logging.getLogger(__name__)


def _setup_logging(log_dir: pathlib.Path) -> pathlib.Path:
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    log_path = log_dir / f"run_{timestamp}.log"
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[logging.FileHandler(log_path), logging.StreamHandler()],
    )
    return log_path


def run_from_config(config_path: pathlib.Path) -> None:
    config = yaml.safe_load(config_path.read_text())
    run_from_config_dict(config, config_path)


def run_from_config_dict(config: dict, config_path: pathlib.Path | None = None) -> None:
    output_dir = pathlib.Path(config.get("output_dir", "outputs"))
    output_dir.mkdir(parents=True, exist_ok=True)
    log_path = _setup_logging(pathlib.Path(config.get("log_dir", "logs")))
    if config_path:
        LOGGER.info("Loaded config from %s", config_path)
    else:
        LOGGER.info("Loaded config from dict")

    online_cfg = config.get("online", {})
    local_paths = [pathlib.Path(p) for p in config.get("local_paths", [])]
    query = config.get("query", [])
    if isinstance(query, str):
        query = [query]

    retriever = OnlineRetriever(online_cfg)
    LOGGER.info("Stage 1/6: online retrieval starting")
    papers, downloads = retriever.search_and_fetch(query)
    LOGGER.info("Stage 1/6: online retrieval complete (papers=%s, downloads=%s)", len(papers), len(downloads))

    LOGGER.info("Stage 2/6: local + downloaded document loading")
    documents = load_documents(local_paths + downloads)
    LOGGER.info("Stage 2/6: document loading complete (documents=%s)", len(documents))

    LOGGER.info("Stage 3/6: chunking documents")
    chunks = chunk_documents(documents)
    LOGGER.info("Stage 3/6: chunking complete (chunks=%s)", len(chunks))

    LOGGER.info("Stage 4/6: candidate filtering")
    candidates = find_candidates(chunks)
    LOGGER.info("Stage 4/6: candidate filtering complete (candidates=%s)", len(candidates))

    extraction_config = config.get("llm", {})
    paper_lookup = {paper.file_path: paper for paper in papers if paper.file_path}
    LOGGER.info("Stage 5/6: extraction starting (llm=%s)", bool(extraction_config.get("enable", False)))
    records = extract_records(candidates, extraction_config, paper_lookup)
    LOGGER.info("Stage 5/6: extraction complete (records=%s)", len(records))
    merged_records = deduplicate_records(records)
    LOGGER.info("Stage 5/6: deduplication complete (records=%s)", len(merged_records))

    LOGGER.info("Stage 6/6: writing outputs")
    write_outputs(output_dir, papers, merged_records)
    report_path = build_report(output_dir, papers, merged_records)
    LOGGER.info("Stage 6/6: outputs written (report=%s)", report_path)

    run_meta = {
        "run_timestamp": datetime.utcnow().isoformat(),
        "log_path": str(log_path),
        "report_path": str(report_path),
        "papers": len(papers),
        "records": len(merged_records),
    }
    (output_dir / "run_meta.json").write_text(json.dumps(run_meta, indent=2, ensure_ascii=False))
    LOGGER.info("Run complete with %s papers and %s records", len(papers), len(merged_records))
