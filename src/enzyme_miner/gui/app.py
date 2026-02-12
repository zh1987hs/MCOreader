import json
import pathlib
import sys

import streamlit as st

REPO_ROOT = pathlib.Path(__file__).resolve().parents[3]
SRC_PATH = REPO_ROOT / "src"
if str(SRC_PATH) not in sys.path:
    sys.path.insert(0, str(SRC_PATH))

from enzyme_miner.cli import run_from_config_dict


st.set_page_config(page_title="Enzyme Miner GUI", layout="wide")

st.title("Enzyme Miner GUI")

with st.sidebar:
    st.header("Online Retrieval")
    query = st.text_area("Query (one per line)", "multicopper oxidase\nlaccase")
    max_papers = st.number_input("Max papers", min_value=1, max_value=200, value=5)
    unpaywall_email = st.text_input("Unpaywall email", "")
    download_dir = st.text_input("Download dir", "./data/raw")
    rate_limit_s = st.number_input("Rate limit (s)", min_value=0.0, value=1.0)

    st.header("Local Paths")
    local_paths = st.text_area("Local paths (one per line)", "./data/local_papers")
    upload_dir = st.text_input("Upload dir", "./data/uploads")
    uploaded_files = st.file_uploader(
        "Upload local files (PDF/DOCX/HTML/TXT)",
        type=["pdf", "docx", "html", "htm", "txt"],
        accept_multiple_files=True,
    )
    scan_enable = st.checkbox("Auto-scan local folders", value=False)
    scan_paths = st.text_area("Scan paths (one per line)", "./data/downloads")

    st.header("Output")
    output_dir = st.text_input("Output dir", "./data/output_demo")
    log_dir = st.text_input("Log dir", "./logs")

    st.header("LLM Settings")
    llm_enable = st.checkbox("Enable LLM extraction", value=True)
    provider = st.selectbox("Provider", ["openai", "openai_compatible"], index=0)
    model = st.text_input("Model", "gpt-4o-mini")
    api_key = st.text_input("API Key (optional, else use env)", "", type="password")
    api_base = st.text_input("API Base", "https://api.openai.com/v1")
    api_key_header = st.text_input("API Key Header", "Authorization")
    api_key_prefix = st.text_input("API Key Prefix", "Bearer")
    response_json_path = st.text_input("Response JSON Path", "choices.0.message.content")
    response_format = st.text_input("Response Format (json_object)", "json_object")
    tolerate_errors = st.checkbox("Tolerate LLM parse errors", value=True)
    temperature = st.number_input("Temperature", min_value=0.0, max_value=2.0, value=0.0)
    max_tokens = st.number_input("Max tokens", min_value=256, max_value=8192, value=1200)
    enzyme_family = st.text_input("Enzyme family", "multicopper oxidase")
    gene_names_possible = st.text_input("Gene names (comma separated)", "mcoA,cueO,mnxG")
    substrate_dictionary = st.text_input("Substrate dictionary path", "./substrate_dictionary.yaml")

st.subheader("Run Configuration")
local_path_list = [p.strip() for p in local_paths.splitlines() if p.strip()]
if uploaded_files:
    upload_path = pathlib.Path(upload_dir)
    upload_path.mkdir(parents=True, exist_ok=True)
    saved_files = []
    for uploaded in uploaded_files:
        target = upload_path / uploaded.name
        target.write_bytes(uploaded.getbuffer())
        saved_files.append(str(target))
    local_path_list.extend(saved_files)

config = {
    "query": [q.strip() for q in query.splitlines() if q.strip()],
    "local_paths": local_path_list,
    "max_papers": int(max_papers),
    "output_dir": output_dir,
    "log_dir": log_dir,
    "online": {
        "max_papers": int(max_papers),
        "unpaywall_email": unpaywall_email,
        "download_dir": download_dir,
        "rate_limit_s": float(rate_limit_s),
    },
    "local_scan": {
        "enable": scan_enable,
        "paths": [p.strip() for p in scan_paths.splitlines() if p.strip()],
    },
    "llm": {
        "enable": llm_enable,
        "provider": provider,
        "model": model,
        "api_key": api_key or None,
        "api_base": api_base,
        "api_key_header": api_key_header,
        "api_key_prefix": api_key_prefix,
        "response_json_path": response_json_path or None,
        "response_format": response_format or None,
        "tolerate_errors": tolerate_errors,
        "temperature": float(temperature),
        "max_tokens": int(max_tokens),
        "extract_prompt_path": "src/enzyme_miner/extraction/prompts/extract_prompt.txt",
        "repair_prompt_path": "src/enzyme_miner/extraction/prompts/repair_prompt.txt",
        "substrate_dictionary": substrate_dictionary,
        "enzyme_family": enzyme_family,
        "gene_names_possible": [g.strip() for g in gene_names_possible.split(",") if g.strip()],
    },
}

st.code(json.dumps(config, indent=2, ensure_ascii=False), language="json")

if st.button("Run Pipeline"):
    with st.spinner("Running pipeline..."):
        run_from_config_dict(config)
    st.success("Run complete. Check output directory for results.")
    output_path = pathlib.Path(output_dir)
    if output_path.exists():
        st.write("Output files:")
        for path in sorted(output_path.glob("*")):
            st.write(f"- {path}")
