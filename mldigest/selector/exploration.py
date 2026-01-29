"""Exploration selection."""
from __future__ import annotations

from typing import List, Tuple

from mldigest.models import Paper
from mldigest.signals.engineering import apply_engineering_signals
from mldigest.signals.keywords import novelty_keyword_hit
from mldigest.signals.recency import recency_score


def score_exploration(
    paper: Paper,
    window_days: int,
    weights: dict,
    buckets: dict,
    topic_diversity_bonus: float,
) -> float:
    apply_engineering_signals(paper)
    novelty = novelty_keyword_hit(paper, buckets)
    recency = recency_score(paper.published_at, window_days)
    has_code = 1.0 if paper.signals.get("engineering", {}).get("has_code_link") else 0.0
    score = (
        weights.get("novelty_keywords", 0.4) * novelty
        + weights.get("recency", 0.3) * recency
        + weights.get("has_code_link", 0.2) * has_code
        + weights.get("topic_diversity", 0.1) * topic_diversity_bonus
    )
    paper.scores["exploration"] = score
    return score


def select_exploration(
    papers: List[Paper],
    window_days: int,
    weights: dict,
    buckets: dict,
    selected_topics: list[str],
) -> Tuple[Paper | None, list[tuple[str, float, dict]]]:
    candidates = []
    for paper in papers:
        topic_diversity_bonus = 0.0
        if paper.topics:
            if not set(paper.topics).intersection(set(selected_topics)):
                topic_diversity_bonus = 1.0
        score_exploration(paper, window_days, weights, buckets, topic_diversity_bonus)
        candidates.append(paper)
    ranked = sorted(candidates, key=lambda p: p.scores.get("exploration", 0), reverse=True)
    debug = [
        (p.paper_id, p.scores.get("exploration", 0), p.signals.get("engineering", {}))
        for p in ranked[:10]
    ]
    return (ranked[0] if ranked else None, debug)
