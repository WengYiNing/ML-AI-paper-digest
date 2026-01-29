"""Artifacts storage."""
from __future__ import annotations

import json
from dataclasses import asdict
from datetime import datetime
from pathlib import Path

from mldigest.models import Paper


def write_artifacts(
    runs_dir: str,
    papers: list[Paper],
    html: str,
    text: str,
    payload: dict,
) -> dict:
    runs_path = Path(runs_dir)
    runs_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base = runs_path / f"digest_{timestamp}"

    json_path = base.with_suffix(".json")
    html_path = base.with_suffix(".html")
    text_path = base.with_suffix(".txt")

    payload = dict(payload)
    payload["selected"] = [asdict(paper) for paper in papers]

    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    html_path.write_text(html, encoding="utf-8")
    text_path.write_text(text, encoding="utf-8")

    return {
        "json": str(json_path),
        "html": str(html_path),
        "text": str(text_path),
    }
