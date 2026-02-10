import logging
from typing import Any

import requests

from enzyme_miner.storage.paper_store import PaperMetadata

LOGGER = logging.getLogger(__name__)

PUBMED_ESEARCH = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
PUBMED_ESUMMARY = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"


def search_pubmed(query: str, max_papers: int = 20) -> list[str]:
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": max_papers,
        "retmode": "json",
    }
    response = requests.get(PUBMED_ESEARCH, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("esearchresult", {}).get("idlist", [])


def fetch_pubmed_metadata(pmids: list[str]) -> list[PaperMetadata]:
    if not pmids:
        return []
    params = {
        "db": "pubmed",
        "id": ",".join(pmids),
        "retmode": "json",
    }
    response = requests.get(PUBMED_ESUMMARY, params=params, timeout=30)
    response.raise_for_status()
    data = response.json().get("result", {})
    papers: list[PaperMetadata] = []
    for pmid in pmids:
        item: dict[str, Any] = data.get(pmid, {})
        if not item:
            continue
        paper = PaperMetadata(
            paper_id=f"pmid:{pmid}",
            doi=None,
            title=item.get("title"),
            journal=item.get("fulljournalname"),
            year=_extract_year(item.get("pubdate")),
            url=f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
            open_access=None,
            fulltext_source="none",
            abstract=item.get("summary"),
        )
        paper.doi = _extract_doi(item.get("articleids", []))
        paper.pmcid = _extract_pmcid(item.get("articleids", []))
        papers.append(paper)
    return papers


def _extract_year(pubdate: str | None) -> int | None:
    if not pubdate:
        return None
    for token in pubdate.split():
        if token.isdigit() and len(token) == 4:
            return int(token)
    return None


def _extract_doi(article_ids: list[dict[str, Any]]) -> str | None:
    for entry in article_ids:
        if entry.get("idtype") == "doi":
            return entry.get("value")
    return None


def _extract_pmcid(article_ids: list[dict[str, Any]]) -> str | None:
    for entry in article_ids:
        if entry.get("idtype") == "pmc":
            return entry.get("value")
    return None
