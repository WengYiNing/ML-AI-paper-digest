"""OpenReview ingestion client."""
from __future__ import annotations

from typing import List

import requests

from mldigest.models import Paper
from mldigest.utils import get_logger

logger = get_logger(__name__)


def _extract_value(field, default=None):
    if isinstance(field, dict):
        return field.get("value", default)
    return field if field is not None else default


def _notes_from_rest(venue: str) -> list[dict]:
    url = "https://api.openreview.net/notes"
    params = {"content.venue": venue, "limit": 200}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    return data.get("notes", [])


def _decision_from_rest(note_id: str) -> dict:
    url = "https://api.openreview.net/notes"
    params = {"forum": note_id, "limit": 50}
    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()
    data = response.json()
    for note in data.get("notes", []):
        content = note.get("content", {})
        if "decision" in content:
            return {
                "decision": _extract_value(content.get("decision")),
                "mean_rating": _extract_value(content.get("mean_rating")),
                "confidence": _extract_value(content.get("confidence")),
            }
    return {}


def fetch_openreview_papers(venues: list[str], accept_only: bool = True) -> List[Paper]:
    papers: list[Paper] = []
    try:
        import openreview  # type: ignore

        client = openreview.api.OpenReviewClient(baseurl="https://api.openreview.net")
        for venue in venues:
            notes = client.get_all_notes(content={"venue": venue})
            for note in notes:
                content = note.content or {}
                decision = content.get("decision")
                if isinstance(decision, dict):
                    decision = decision.get("value")
                if accept_only and decision and "accept" not in str(decision).lower():
                    continue
                openreview_url = f"https://openreview.net/forum?id={note.id}"
                signals = {
                    "openreview": {
                        "venue": venue,
                        "decision": decision,
                        "mean_rating": content.get("mean_rating", {}).get("value")
                        if isinstance(content.get("mean_rating"), dict)
                        else content.get("mean_rating"),
                        "confidence": content.get("confidence", {}).get("value")
                        if isinstance(content.get("confidence"), dict)
                        else content.get("confidence"),
                    }
                }
                papers.append(
                    Paper(
                        paper_id=f"openreview:{note.id}",
                        title=content.get("title", {}).get("value", ""),
                        authors=content.get("authors", {}).get("value", []),
                        abstract=content.get("abstract", {}).get("value"),
                        published_at=note.pdate,
                        categories=[venue],
                        links={"openreview_url": openreview_url},
                        source_tags=["openreview"],
                        signals=signals,
                    )
                )
        return papers
    except Exception as exc:  # pragma: no cover - fallback for runtime
        logger.warning("OpenReview client failed, fallback to REST: %s", exc)

    for venue in venues:
        try:
            notes = _notes_from_rest(venue)
        except Exception as exc:  # pragma: no cover - network failure
            logger.warning("OpenReview REST failed for venue %s: %s", venue, exc)
            continue
        for note in notes:
            content = note.get("content", {})
            decision_info = {}
            if accept_only:
                try:
                    decision_info = _decision_from_rest(note.get("id"))
                except Exception as exc:  # pragma: no cover
                    logger.warning("OpenReview decision fetch failed: %s", exc)
            decision = decision_info.get("decision") or _extract_value(content.get("decision"))
            if accept_only and decision and "accept" not in str(decision).lower():
                continue
            openreview_url = f"https://openreview.net/forum?id={note.get('id')}"
            signals = {
                "openreview": {
                    "venue": venue,
                    "decision": decision,
                    "mean_rating": decision_info.get("mean_rating"),
                    "confidence": decision_info.get("confidence"),
                }
            }
            papers.append(
                Paper(
                    paper_id=f"openreview:{note.get('id')}",
                    title=_extract_value(content.get("title"), ""),
                    authors=_extract_value(content.get("authors"), []),
                    abstract=_extract_value(content.get("abstract")),
                    published_at=note.get("pdate"),
                    categories=[venue],
                    links={"openreview_url": openreview_url},
                    source_tags=["openreview"],
                    signals=signals,
                )
            )
    return papers
