import logging
import pathlib
import time
from dataclasses import dataclass
from typing import Any

import requests

from enzyme_miner.ingestion.pubmed import fetch_pubmed_metadata, search_pubmed
from enzyme_miner.ingestion.pmc import fetch_pmc_xml
from enzyme_miner.storage.paper_store import PaperMetadata

LOGGER = logging.getLogger(__name__)

CROSSREF_API = "https://api.crossref.org/works"
UNPAYWALL_API = "https://api.unpaywall.org/v2"


@dataclass
class OnlineRetriever:
    config: dict[str, Any]

    def search_and_fetch(self, queries: list[str]) -> tuple[list[PaperMetadata], list[pathlib.Path]]:
        max_papers = int(self.config.get("max_papers", 10))
        email = self.config.get("unpaywall_email", "")
        download_dir = pathlib.Path(self.config.get("download_dir", "data/raw"))
        download_dir.mkdir(parents=True, exist_ok=True)
        rate_limit_s = float(self.config.get("rate_limit_s", 1.0))

        papers: list[PaperMetadata] = []
        downloads: list[pathlib.Path] = []

        total_queries = len(queries)
        for idx, query in enumerate(queries, start=1):
            LOGGER.info("Online retrieval %s/%s: query=%s", idx, total_queries, query)
            LOGGER.info("Searching Crossref for query: %s", query)
            crossref_papers = self._search_crossref(query, max_papers)
            LOGGER.info("Crossref returned %s records", len(crossref_papers))
            for paper in crossref_papers:
                if paper.doi and email:
                    oa_info = self._fetch_unpaywall(paper.doi, email)
                    paper.open_access = oa_info.get("is_oa")
                    best_location = oa_info.get("best_oa_location") or {}
                    paper.url = best_location.get("url") or paper.url
                    paper.fulltext_source = "unpaywall" if paper.open_access else "none"
                    pdf_url = best_location.get("url_for_pdf")
                    if pdf_url:
                        pdf_path = self._download_file(pdf_url, download_dir, suffix=".pdf")
                        if pdf_path:
                            paper.file_path = str(pdf_path)
                            downloads.append(pdf_path)
                papers.append(paper)
            time.sleep(rate_limit_s)

            LOGGER.info("Searching PubMed for query: %s", query)
            pmids = search_pubmed(query, max_papers=max_papers)
            LOGGER.info("PubMed returned %s PMIDs", len(pmids))
            pm_papers = fetch_pubmed_metadata(pmids)
            LOGGER.info("PubMed metadata fetched for %s records", len(pm_papers))
            for paper in pm_papers:
                if paper.doi and email:
                    oa_info = self._fetch_unpaywall(paper.doi, email)
                    paper.open_access = oa_info.get("is_oa")
                    best_location = oa_info.get("best_oa_location") or {}
                    paper.url = best_location.get("url") or paper.url
                    paper.fulltext_source = "unpaywall" if paper.open_access else "none"
                    pdf_url = best_location.get("url_for_pdf")
                    if pdf_url:
                        pdf_path = self._download_file(pdf_url, download_dir, suffix=".pdf")
                        if pdf_path:
                            paper.file_path = str(pdf_path)
                            downloads.append(pdf_path)
                papers.append(paper)
            time.sleep(rate_limit_s)

        for paper in papers:
            if paper.pmcid:
                LOGGER.info("Fetching PMC XML for %s", paper.pmcid)
                xml_path = fetch_pmc_xml(paper.pmcid, download_dir)
                if xml_path:
                    paper.fulltext_source = "pmc"
                    paper.file_path = str(xml_path)
                    downloads.append(xml_path)

        return papers[:max_papers], downloads

    def _search_crossref(self, query: str, max_papers: int) -> list[PaperMetadata]:
        params = {"query": query, "rows": max_papers}
        response = requests.get(CROSSREF_API, params=params, timeout=30)
        response.raise_for_status()
        data = response.json()
        items = data.get("message", {}).get("items", [])
        papers: list[PaperMetadata] = []
        for item in items:
            papers.append(
                PaperMetadata(
                    paper_id=None,
                    doi=item.get("DOI"),
                    title=(item.get("title") or [None])[0],
                    journal=(item.get("container-title") or [None])[0],
                    year=(item.get("issued", {}).get("date-parts", [[None]])[0][0]),
                    url=item.get("URL"),
                    open_access=None,
                    fulltext_source="none",
                )
            )
        return papers

    def _fetch_unpaywall(self, doi: str, email: str) -> dict[str, Any]:
        url = f"{UNPAYWALL_API}/{doi}"
        response = requests.get(url, params={"email": email}, timeout=30)
        if response.status_code != 200:
            LOGGER.warning("Unpaywall lookup failed for DOI %s", doi)
            return {}
        return response.json()

    def _download_file(self, url: str, download_dir: pathlib.Path, suffix: str) -> pathlib.Path | None:
        try:
            response = requests.get(url, timeout=60)
            response.raise_for_status()
        except requests.RequestException as exc:
            LOGGER.warning("Failed to download %s: %s", url, exc)
            return None
        filename = url.split("/")[-1].split("?")[0]
        if not filename.endswith(suffix):
            filename = f"{filename}{suffix}"
        path = download_dir / filename
        path.write_bytes(response.content)
        return path
