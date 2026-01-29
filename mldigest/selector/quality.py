"""Quality selection."""
from __future__ import annotations

from typing import List, Tuple

from mldigest.models import Paper
from mldigest.signals.recency import recency_score


def score_quality(paper: Paper, window_days: int, venue_bonus: dict) -> float:
    signal = paper.signals.get("openreview", {}) if paper.signals else {}
    mean_rating = signal.get("mean_rating") or 0
    venue = signal.get("venue", "")
    bonus = 0.0
    for key, value in venue_bonus.items():
        if key.lower() in venue.lower():
            bonus = max(bonus, float(value))
    recency = recency_score(paper.published_at, window_days)
    score = float(mean_rating) + bonus + recency
    paper.scores["quality"] = score
    return score


def select_quality(
    papers: List[Paper],
    window_days: int,
    venue_bonus: dict,
) -> Tuple[Paper | None, list[tuple[str, float, dict]]]:
    for paper in papers:
        score_quality(paper, window_days, venue_bonus)
    ranked = sorted(papers, key=lambda p: p.scores.get("quality", 0), reverse=True)
    debug = [(p.paper_id, p.scores.get("quality", 0), p.signals.get("openreview", {})) for p in ranked[:10]]
    return (ranked[0] if ranked else None, debug)
