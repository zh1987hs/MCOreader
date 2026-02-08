# Enzyme Miner (MCO example)

A compliant pipeline for automatically collecting and extracting enzyme substrate specificity and kinetic parameters from **open-access online resources** and **local files**.

## Project structure

```
src/
  enzyme_miner/
    ingestion/         # Online retrieval (Crossref/Unpaywall)
    parsing/           # PDF/DOCX/HTML/TXT parsing
    chunking/          # Chunk documents for retrieval
    candidate_finder/  # Keyword filtering for candidate chunks
    extraction/        # LLM prompts + schema validation
    normalization/     # Substrate normalization, unit conversion, dedup
    storage/           # CSV/JSONL/SQLite writers
    reporting/         # Markdown report builder
```

## Key module design

- `ingestion/online.py`: Crossref/PubMed/PMC search + Unpaywall OA checks; **no paywall bypass**.
- `parsing/*_parser.py`: Load PDF/DOCX/HTML/TXT, keeping minimal metadata.
- `chunking/chunker.py`: Paragraph-based chunking with location hints.
- `candidate_finder/candidates.py`: Regex keywords to identify candidate regions.
- `extraction/extractor.py`: Heuristic extractor + schema validation; LLM-ready prompts in `extraction/prompts/`.
- `normalization/`: Substrate synonyms and unit conversions; deduplication by paper/enzyme/substrate/parameter.
- `storage/writer.py`: Outputs `records.jsonl`, `records.csv`, `records.sqlite`, `papers.csv`.
- `reporting/report.py`: Summary report with distributions and review list.

## Install

```bash
pip install -r requirements.txt
```

## Run (CLI)

```bash
python -m enzyme_miner --config config.example.yaml
```

## GUI 使用方式

使用 Streamlit 启动图形界面：

```bash
streamlit run -m enzyme_miner.gui
```

GUI 中可填写检索关键词、下载目录、输出目录、模型 API 等参数，并点击 “Run Pipeline” 启动完整流程。

## 中文使用说明（在线检索 + LLM 抽取）

1) 配置 `config.example.yaml`（可复制改名为 `config.yaml`）：
   - `online.unpaywall_email` 填写有效邮箱（Unpaywall 需要）。  
   - `online.download_dir` 指向下载缓存目录（默认 `data/raw`）。  
   - `llm.enable: true`，并在环境变量中设置 `OPENAI_API_KEY`，或直接填写 `llm.api_key`。  
   - 可在 `llm.gene_names_possible` 与 `llm.enzyme_family` 填写目标酶关键词。

2) 运行：
```bash
export OPENAI_API_KEY="your_key"
python -m enzyme_miner --config config.example.yaml
```

3) 输出：
   - `records.jsonl` / `records.csv` / `records.sqlite`：结构化记录  
   - `papers.csv`：文献元数据（含 OA 与全文来源标注）  
   - `report.md`：统计与需人工复核列表

## Configuration

See `config.example.yaml` for:
- `query`: enzyme family/keywords
- `local_paths`: directories with PDFs/HTML/TXT/DOCX
- `output_dir`: output location
- `online.unpaywall_email`: required for Unpaywall
- `online.download_dir`: cache path for OA PDF/PMC XML
- `llm`: enable LLM extraction + API configuration (supports OpenAI-compatible endpoints)
  - `llm.response_json_path`: optional JSON path to extract content from API response (e.g. `choices.0.message.content`)

## Outputs

- `records.jsonl`: per-record structured extraction
- `records.csv`: flattened table
- `records.sqlite`: SQLite database (raw + flattened JSON per row)
- `papers.csv`: metadata and availability status
- `report.md`: summary report
- `run_meta.json`: run metadata

## Substrate dictionary

Provide `substrate_dictionary.yaml` or `.json` with normalized names + synonyms + category.
If missing, defaults are used (ABTS, 2,6-DMP, SGZ, Mn(II), Fe(II), etc.).

## Compliance

- No paywall bypassing or login scraping.
- Unavailable full text is recorded as metadata only (`fulltext_source: none`).
- Evidence snippets are limited to <= 300 chars.

## Demo output

See `data/output_demo/` for example `papers.csv`, `records.jsonl`, and `report.md`.

## Tests

```bash
python -m unittest
```
