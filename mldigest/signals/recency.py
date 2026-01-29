"""Recency signal."""
from __future__ import annotations

from mldigest.utils import days_since


def recency_score(published_at: str | None, window_days: int) -> float:
    days = days_since(published_at)
    if days is None:
        return 0.0
    return max(0.0, (window_days - days) / window_days)
