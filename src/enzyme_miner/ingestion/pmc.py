import logging
import pathlib

import requests

LOGGER = logging.getLogger(__name__)

PMC_EFETCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"


def fetch_pmc_xml(pmcid: str, download_dir: pathlib.Path) -> pathlib.Path | None:
    if not pmcid:
        return None
    params = {
        "db": "pmc",
        "id": pmcid.replace("PMC", ""),
        "retmode": "xml",
    }
    try:
        response = requests.get(PMC_EFETCH, params=params, timeout=60)
        response.raise_for_status()
    except requests.RequestException as exc:
        LOGGER.warning("Failed to fetch PMC XML for %s: %s", pmcid, exc)
        return None
    path = download_dir / f"{pmcid}.xml"
    path.write_text(response.text, encoding="utf-8")
    return path
