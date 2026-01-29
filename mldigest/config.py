"""Configuration loader and validator."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict

import yaml


class ConfigError(ValueError):
    """Raised when configuration validation fails."""


@dataclass
class Config:
    data: Dict[str, Any]

    def __getitem__(self, item: str) -> Any:
        return self.data[item]


def _require(config: Dict[str, Any], key: str, path: str) -> Any:
    if key not in config:
        raise ConfigError(f"Missing required config field: {path}{key}")
    return config[key]


def _require_dict(config: Dict[str, Any], key: str, path: str) -> Dict[str, Any]:
    value = _require(config, key, path)
    if not isinstance(value, dict):
        raise ConfigError(f"Expected dict at {path}{key}")
    return value


def _require_list(config: Dict[str, Any], key: str, path: str) -> list:
    value = _require(config, key, path)
    if not isinstance(value, list):
        raise ConfigError(f"Expected list at {path}{key}")
    return value


def validate_config(cfg: Dict[str, Any]) -> None:
    schedule = _require_dict(cfg, "schedule", "")
    _require(schedule, "mode", "schedule.")
    _require(schedule, "timezone", "schedule.")
    _require(schedule, "window_days", "schedule.")

    limits = _require_dict(cfg, "limits", "")
    _require(limits, "papers_per_cycle", "limits.")
    _require(limits, "arxiv_max_results", "limits.")
    _require(limits, "per_topic_cap", "limits.")
    _require(limits, "enable_keyphrases", "limits.")

    sources = _require_dict(cfg, "sources", "")
    arxiv = _require_dict(sources, "arxiv", "sources.")
    _require(arxiv, "enabled", "sources.arxiv.")
    _require_list(arxiv, "categories", "sources.arxiv.")

    hf = _require_dict(sources, "hf", "sources.")
    _require(hf, "enabled", "sources.hf.")

    openreview = _require_dict(sources, "openreview", "sources.")
    _require(openreview, "enabled", "sources.openreview.")
    _require_list(openreview, "venues", "sources.openreview.")
    _require(openreview, "accept_only", "sources.openreview.")

    topics = _require_dict(cfg, "topics", "")
    _require(topics, "method", "topics.")
    buckets = _require_dict(topics, "buckets", "topics.")
    if not buckets:
        raise ConfigError("topics.buckets must not be empty")

    selection = _require_dict(cfg, "selection_strategy", "")
    trending = _require_dict(selection, "trending", "selection_strategy.")
    _require_dict(trending, "weights", "selection_strategy.trending.")
    _require(trending, "fallback", "selection_strategy.trending.")
    quality = _require_dict(selection, "quality", "selection_strategy.")
    _require_dict(quality, "venue_bonus", "selection_strategy.quality.")
    _require_list(quality, "tie_break", "selection_strategy.quality.")
    exploration = _require_dict(selection, "exploration", "selection_strategy.")
    _require_dict(exploration, "weights", "selection_strategy.exploration.")

    email = _require_dict(cfg, "email", "")
    _require(email, "enabled", "email.")
    _require(email, "from_name", "email.")
    _require(email, "from_address", "email.")
    _require_list(email, "to_addresses", "email.")
    _require(email, "smtp_host", "email.")
    _require(email, "smtp_port", "email.")
    _require(email, "use_tls", "email.")
    _require(email, "subject_prefix", "email.")

    storage = _require_dict(cfg, "storage", "")
    _require(storage, "runs_dir", "storage.")


def load_config(path: str | Path) -> Config:
    path = Path(path)
    if not path.exists():
        raise ConfigError(f"Config file not found: {path}")
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}
    if not isinstance(data, dict):
        raise ConfigError("Config root must be a mapping")
    validate_config(data)
    return Config(data=data)


def masked_config(cfg: Dict[str, Any]) -> Dict[str, Any]:
    masked = dict(cfg)
    email = dict(masked.get("email", {}))
    if "from_address" in email:
        email["from_address"] = "***"
    if "to_addresses" in email:
        email["to_addresses"] = ["***" for _ in email["to_addresses"]]
    masked["email"] = email
    return masked
