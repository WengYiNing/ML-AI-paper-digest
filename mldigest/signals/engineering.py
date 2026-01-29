"""Engineering-related signals."""
from __future__ import annotations

from mldigest.models import Paper


KEYWORDS = {
    "inference": ["inference", "serving"],
    "latency": ["latency"],
    "memory": ["memory", "compression"],
    "training": ["training", "optimization"],
}


def apply_engineering_signals(paper: Paper) -> None:
    text = f"{paper.title} {paper.abstract or ''}".lower()
    has_code_link = False
    for url in paper.links.values():
        if "github.com" in url:
            has_code_link = True
            break
    if not has_code_link and "github.com" in text:
        has_code_link = True
    signals = paper.signals.setdefault("engineering", {})
    signals["has_code_link"] = has_code_link
    for name, keywords in KEYWORDS.items():
        signals[f"mentions_{name}"] = any(keyword in text for keyword in keywords)
