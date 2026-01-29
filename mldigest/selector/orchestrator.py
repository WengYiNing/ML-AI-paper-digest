"""Main orchestration for selecting papers."""
from __future__ import annotations

from typing import Dict, List, Tuple
import random

from mldigest.models import Paper
from mldigest.selector.quality import select_quality
from mldigest.selector.trending import select_trending
from mldigest.signals.hf_signal import apply_hf_signal
from mldigest.signals.keywords import assign_topics
from mldigest.signals.recency import recency_score
from mldigest.utils import dedupe_arxiv_id, fuzzy_title_match, normalize_title


def _merge_by_key(existing: dict[str, Paper], key: str, paper: Paper) -> None:
    if key in existing:
        existing[key].merge_sources(paper)
    else:
        existing[key] = paper


def merge_papers(arxiv_papers: List[Paper], openreview_papers: List[Paper]) -> List[Paper]:
    merged: dict[str, Paper] = {}
    for paper in arxiv_papers:
        arxiv_id = paper.signals.get("arxiv_id") or paper.paper_id.replace("arxiv:", "")
        _merge_by_key(merged, f"arxiv:{dedupe_arxiv_id(arxiv_id)}", paper)
    for paper in openreview_papers:
        matched = False
        for existing in list(merged.values()):
            if fuzzy_title_match(existing.title, paper.title):
                existing.merge_sources(paper)
                matched = True
                break
        if not matched:
            _merge_by_key(merged, normalize_title(paper.title), paper)
    return list(merged.values())


def _fallback_trending(papers: List[Paper], window_days: int, buckets: dict) -> Paper | None:
    scored = []
    for paper in papers:
        assign_topics(paper, buckets)
        topic_bonus = 1 if paper.topics else 0
        score = recency_score(paper.published_at, window_days) + topic_bonus
        paper.scores["trending_fallback"] = score
        scored.append(paper)
    ranked = sorted(scored, key=lambda p: p.scores.get("trending_fallback", 0), reverse=True)
    return ranked[0] if ranked else None


def _selection_reason_recency(paper: Paper, window_days: int) -> str | None:
    if not paper.published_at:
        return None
    days = int(window_days * (1 - recency_score(paper.published_at, window_days)))
    return f"近期發佈: {days} 天內"


def orchestrate_selection(
    arxiv_papers: List[Paper],
    openreview_papers: List[Paper],
    hf_hits: Dict[str, dict],
    config: dict,
) -> Tuple[List[Paper], dict]:
    merged_candidates = merge_papers(arxiv_papers, openreview_papers)
    buckets = config["topics"]["buckets"]
    window_days = config["schedule"]["window_days"]

    for paper in merged_candidates:
        assign_topics(paper, buckets)
        apply_hf_signal(paper, hf_hits)

    trending_weights = config["selection_strategy"]["trending"]["weights"]
    trending, trending_debug = select_trending(merged_candidates, hf_hits, window_days, trending_weights)
    if not trending:
        trending = _fallback_trending(merged_candidates, window_days, buckets)

    selected: list[Paper] = []
    scoring_debug = {
        "trending": trending_debug,
        "quality": [],
        "exploration": [],
    }

    if trending:
        hf_signal = trending.signals.get("hf", {})
        if hf_signal:
            trending.selection_reasons.append(f"HF 命中: {', '.join(hf_signal.get('query_hits', []))}")
        else:
            trending.selection_reasons.append("HF 未命中，使用 arXiv 近期 + 主題 fallback")
        recency_reason = _selection_reason_recency(trending, window_days)
        if recency_reason:
            trending.selection_reasons.append(recency_reason)
        if trending.topics:
            trending.selection_reasons.append(f"主題: {'/'.join(trending.topics)}")
        trending.signals["role"] = "trending"
        selected.append(trending)

    quality, quality_debug = select_quality(
        openreview_papers,
        window_days,
        config["selection_strategy"]["quality"]["venue_bonus"],
    )
    scoring_debug["quality"] = quality_debug
    if quality and trending and fuzzy_title_match(quality.title, trending.title):
        quality = None
    if not quality:
        fallback_pool = [paper for paper in merged_candidates if paper not in selected]
        quality = _fallback_trending(fallback_pool, window_days, buckets)
        if quality:
            quality.selection_reasons.append("OpenReview 不可用，使用 arXiv 近期 fallback")
    if quality:
        openreview_signal = quality.signals.get("openreview", {})
        if openreview_signal:
            quality.selection_reasons.append(
                f"OpenReview: {openreview_signal.get('venue', '')} {openreview_signal.get('decision', '')}".strip()
            )
        if openreview_signal.get("mean_rating"):
            quality.selection_reasons.append(f"Mean rating: {openreview_signal.get('mean_rating')}")
        recency_reason = _selection_reason_recency(quality, window_days)
        if recency_reason:
            quality.selection_reasons.append(recency_reason)
        if quality.topics:
            quality.selection_reasons.append(f"主題: {'/'.join(quality.topics)}")
        quality.signals["role"] = "quality"
        selected.append(quality)

    exploration_candidates = []
    for paper in arxiv_papers:
        if any(fuzzy_title_match(paper.title, chosen.title) for chosen in selected):
            continue
        if paper.signals.get("hf"):
            continue
        exploration_candidates.append(paper)

    scoring_debug["exploration"] = []
    if exploration_candidates:
        exploration = random.choice(exploration_candidates)
        exploration.selection_reasons.append("未在 HF 上榜（探索）")
        exploration.selection_reasons.append("隨機選擇自 arXiv 候選")
        recency_reason = _selection_reason_recency(exploration, window_days)
        if recency_reason:
            exploration.selection_reasons.append(recency_reason)
        if exploration.topics:
            exploration.selection_reasons.append(f"主題: {'/'.join(exploration.topics)}")
        exploration.signals["role"] = "exploration"
        selected.append(exploration)

    if len(selected) < 3:
        existing_roles = {paper.signals.get("role") for paper in selected}
        missing_roles = [role for role in ["trending", "quality", "exploration"] if role not in existing_roles]
        remaining = [paper for paper in merged_candidates if paper not in selected]
        remaining.sort(key=lambda p: recency_score(p.published_at, window_days), reverse=True)
        for role in missing_roles:
            if not remaining:
                break
            paper = remaining.pop(0)
            paper.selection_reasons.append("候選不足，使用 recency fallback")
            recency_reason = _selection_reason_recency(paper, window_days)
            if recency_reason:
                paper.selection_reasons.append(recency_reason)
            paper.signals["role"] = role
            selected.append(paper)

    return selected, scoring_debug
