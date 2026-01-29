"""Hugging Face papers trending signals."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict

import requests

from mldigest.utils import get_logger, normalize_title

logger = get_logger(__name__)

HF_ENDPOINT = "https://huggingface.co/api/daily_papers"


def fetch_hf_hits(month: str, per_query: int = 50) -> Dict[str, dict]:
    results: dict[str, dict] = defaultdict(lambda: {"matched": True, "query_hits": [], "best_rank_proxy": 0})
    try:
        response = requests.get(HF_ENDPOINT, params={"month": month, "sort": "trending"}, timeout=20)
        response.raise_for_status()
        data = response.json()
    except Exception as exc:  # pragma: no cover - network failure
        logger.warning("HF daily papers failed for %s: %s", month, exc)
        return {}
    if isinstance(data, list):
        items = data
    elif isinstance(data, dict):
        items = data.get("items") or data.get("papers") or data.get("hits") or []
    else:
        items = []
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
        entry["query_hits"].append("daily_trending")
        best_rank = entry.get("best_rank_proxy") or 0
        score = max(0, per_query - rank + 1)
        entry["best_rank_proxy"] = max(best_rank, score)
    return dict(results)
