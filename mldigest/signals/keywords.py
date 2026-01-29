"""Keyword-based topic labeling."""
from __future__ import annotations

from typing import Dict, List

from mldigest.models import Paper


def assign_topics(paper: Paper, buckets: Dict[str, List[str]]) -> List[str]:
    text = f"{paper.title} {paper.abstract or ''}".lower()
    topics: list[str] = []
    for topic, keywords in buckets.items():
        for keyword in keywords:
            if keyword.lower() in text:
                topics.append(topic)
                break
    paper.topics = topics
    return topics


def novelty_keyword_hit(paper: Paper, buckets: Dict[str, List[str]]) -> int:
    if not paper.topics:
        assign_topics(paper, buckets)
    return 1 if paper.topics else 0
