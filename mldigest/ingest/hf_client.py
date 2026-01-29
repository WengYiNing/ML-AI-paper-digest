"""Hugging Face papers trending signals."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict

import requests

from mldigest.utils import get_logger, normalize_title

logger = get_logger(__name__)

HF_ENDPOINT = "https://huggingface.co/api/papers/search"


def fetch_hf_hits(queries: list[str], per_query: int = 20) -> Dict[str, dict]:
    results: dict[str, dict] = defaultdict(lambda: {"matched": True, "query_hits": [], "best_rank_proxy": 0})
    for query in queries:
        try:
            response = requests.get(HF_ENDPOINT, params={"q": query}, timeout=20)
            response.raise_for_status()
            data = response.json()
        except Exception as exc:  # pragma: no cover - network failure
            logger.warning("HF search failed for %s: %s", query, exc)
            continue
        items = (
            data if isinstance(data, list)
            else data.get("items") or data.get("papers") or data.get("hits") or []
        )
        for rank, item in enumerate(items[:per_query], start=1):
            arxiv_id = item.get("arxiv_id") or item.get("arxivId")
            paper_url = item.get("paper_url") or item.get("url") or ""
            title = item.get("title") or ""
            key = None
            if arxiv_id:
                key = f"arxiv:{arxiv_id}"
            elif "arxiv.org" in paper_url:
                key = f"arxiv:{paper_url.split('/')[-1]}"
            elif title:
                key = normalize_title(title)
            if not key:
                continue
            entry = results[key]
            entry["query_hits"].append(query)
            best_rank = entry.get("best_rank_proxy") or 0
            score = max(0, per_query - rank + 1)
            entry["best_rank_proxy"] = max(best_rank, score)
    return dict(results)
