"""OpenReview signals helper."""
from __future__ import annotations

from mldigest.models import Paper


def extract_openreview_signal(paper: Paper) -> dict:
    return paper.signals.get("openreview", {}) if paper.signals else {}
