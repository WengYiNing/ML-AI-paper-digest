"""Utility helpers."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta, timezone
from typing import Iterable, Optional, Tuple

from dateutil import parser
from rapidfuzz import fuzz


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("[%(levelname)s] %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


def normalize_title(title: str) -> str:
    normalized = re.sub(r"\s+", " ", title.strip().lower())
    normalized = re.sub(r"[^a-z0-9 ]", "", normalized)
    return normalized


def fuzzy_title_match(title_a: str, title_b: str, threshold: int = 90) -> bool:
    return fuzz.token_set_ratio(normalize_title(title_a), normalize_title(title_b)) >= threshold


def parse_iso_date(value: Optional[str]) -> Optional[datetime]:
    if not value:
        return None
    try:
        return parser.isoparse(value)
    except (ValueError, TypeError):
        return None


def days_since(iso_date: Optional[str]) -> Optional[int]:
    dt = parse_iso_date(iso_date)
    if not dt:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return max(0, (now - dt).days)


def window_bounds(window_days: int) -> Tuple[datetime, datetime]:
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=window_days)
    return start, end


def filter_by_window(published_at: Optional[str], window_days: int) -> bool:
    if not published_at:
        return False
    dt = parse_iso_date(published_at)
    if not dt:
        return False
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    now = datetime.now(timezone.utc)
    return (now - dt).days <= window_days


def normalize_scores(values: Iterable[float]) -> list[float]:
    values_list = list(values)
    if not values_list:
        return []
    min_val = min(values_list)
    max_val = max(values_list)
    if min_val == max_val:
        return [1.0 for _ in values_list]
    return [(val - min_val) / (max_val - min_val) for val in values_list]


def dedupe_arxiv_id(arxiv_id: str) -> str:
    return re.sub(r"v\d+$", "", arxiv_id)
