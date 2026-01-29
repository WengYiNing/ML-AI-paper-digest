"""arXiv API client."""
from __future__ import annotations

from typing import List

import feedparser
import requests

from mldigest.models import Paper
from mldigest.utils import dedupe_arxiv_id, filter_by_window

ARXIV_API = "https://export.arxiv.org/api/query"


def _build_query(categories: list[str]) -> str:
    parts = [f"cat:{cat}" for cat in categories]
    return " OR ".join(parts)


def fetch_arxiv_papers(
    categories: list[str],
    start: int,
    max_results: int,
    sort_by: str = "submittedDate",
    sort_order: str = "descending",
    window_days: int | None = None,
) -> List[Paper]:
    query = _build_query(categories)
    params = {
        "search_query": query,
        "start": start,
        "max_results": max_results,
        "sortBy": sort_by,
        "sortOrder": sort_order,
    }
    response = requests.get(ARXIV_API, params=params, timeout=30)
    response.raise_for_status()
    feed = feedparser.parse(response.text)
    papers: list[Paper] = []
    for entry in feed.entries:
        arxiv_id = entry.get("id", "").split("/abs/")[-1]
        paper_id = f"arxiv:{arxiv_id}"
        if window_days is not None and not filter_by_window(entry.get("published"), window_days):
            continue
        links = {}
        abs_url = entry.get("link")
        if abs_url:
            links["abs_url"] = abs_url
        pdf_url = None
        for link in entry.get("links", []):
            if link.get("type") == "application/pdf":
                pdf_url = link.get("href")
        if pdf_url:
            links["pdf_url"] = pdf_url
        categories_list = [tag.get("term") for tag in entry.get("tags", []) if tag.get("term")]
        papers.append(
            Paper(
                paper_id=paper_id,
                title=entry.get("title", "").replace("\n", " ").strip(),
                authors=[author.get("name") for author in entry.get("authors", []) if author.get("name")],
                abstract=entry.get("summary", "").replace("\n", " ").strip(),
                published_at=entry.get("published"),
                categories=categories_list,
                links=links,
                source_tags=["arxiv"],
                signals={"arxiv_id": dedupe_arxiv_id(arxiv_id)},
            )
        )
    return papers
