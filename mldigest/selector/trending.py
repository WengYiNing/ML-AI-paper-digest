"""Trending selection."""
from __future__ import annotations

from typing import List, Tuple

from mldigest.models import Paper
from mldigest.signals.recency import recency_score
from mldigest.utils import normalize_title


def score_trending(paper: Paper, window_days: int, weights: dict) -> float:
    hf_signal = paper.signals.get("hf", {}) if paper.signals else {}
    hf_rank = hf_signal.get("best_rank_proxy", 0)
    recency = recency_score(paper.published_at, window_days)
    score = weights.get("hf_rank", 0.6) * hf_rank + weights.get("recency", 0.4) * recency
    paper.scores["trending"] = score
    return score


def select_trending(
    papers: List[Paper],
    hf_hits: dict,
    window_days: int,
    weights: dict,
) -> Tuple[Paper | None, list[tuple[str, float, dict]]]:
    candidates = []
    for paper in papers:
        key = paper.paper_id
        alt_key = normalize_title(paper.title)
        if key in hf_hits or alt_key in hf_hits:
            score = score_trending(paper, window_days, weights)
            candidates.append(paper)
    ranked = sorted(candidates, key=lambda p: p.scores.get("trending", 0), reverse=True)
    debug = [(p.paper_id, p.scores.get("trending", 0), p.signals.get("hf", {})) for p in ranked[:10]]
    return (ranked[0] if ranked else None, debug)
