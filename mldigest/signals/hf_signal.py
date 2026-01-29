"""Apply Hugging Face signals."""
from __future__ import annotations

from mldigest.models import Paper
from mldigest.utils import normalize_title


def apply_hf_signal(paper: Paper, hf_hits: dict[str, dict]) -> None:
    key = paper.paper_id
    alt_key = normalize_title(paper.title)
    hit = hf_hits.get(key) or hf_hits.get(alt_key)
    if hit:
        paper.signals.setdefault("hf", {}).update(hit)
