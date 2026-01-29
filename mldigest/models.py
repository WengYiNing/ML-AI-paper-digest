"""Shared data models."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional


@dataclass
class Paper:
    paper_id: str
    title: str
    authors: List[str]
    abstract: Optional[str]
    published_at: Optional[str]
    categories: List[str]
    links: Dict[str, str]
    source_tags: List[str]
    signals: Dict[str, object] = field(default_factory=dict)
    keyphrases: List[str] = field(default_factory=list)
    topics: List[str] = field(default_factory=list)
    scores: Dict[str, float] = field(default_factory=dict)
    selection_reasons: List[str] = field(default_factory=list)

    def merge_sources(self, other: "Paper") -> None:
        for tag in other.source_tags:
            if tag not in self.source_tags:
                self.source_tags.append(tag)
        for key, value in other.links.items():
            if key not in self.links and value:
                self.links[key] = value
        for key, value in other.signals.items():
            if key not in self.signals:
                self.signals[key] = value
