from __future__ import annotations

from pathlib import Path

import yaml


def normalize_color(value: object, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback

    normalized = value.strip()
    if not normalized:
        return fallback

    return normalized


def normalize_text(value: object, fallback: str) -> str:
    if not isinstance(value, str):
        return fallback

    normalized = value.strip()
    if not normalized:
        return fallback

    return normalized


def normalize_color_list(value: object, fallback: list[str]) -> list[str]:
    if not isinstance(value, list):
        return fallback

    normalized_colors = [
        item.strip() for item in value if isinstance(item, str) and item.strip()
    ]
    return normalized_colors or fallback


def normalize_bool(value: object, fallback: bool) -> bool:
    if isinstance(value, bool):
        return value

    if isinstance(value, str):
        normalized = value.strip().lower()
        if normalized in {"true", "1", "yes", "y", "on"}:
            return True
        if normalized in {"false", "0", "no", "n", "off"}:
            return False

    return fallback


def normalize_positive_int(value: object, fallback: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return fallback

    return parsed if parsed > 0 else fallback


def normalize_choice(value: object, valid_values: set[str], fallback: str) -> str:
    normalized = str(value).strip().lower()
    return normalized if normalized in valid_values else fallback


def read_yaml_dict(path: Path) -> dict:
    if not path.exists():
        return {}

    try:
        with path.open("r", encoding="utf-8") as yaml_file:
            loaded = yaml.safe_load(yaml_file) or {}
    except (OSError, yaml.YAMLError):
        return {}

    return loaded if isinstance(loaded, dict) else {}


def merge_dict(base: dict, updates: dict) -> dict:
    merged = dict(base)
    for key, value in updates.items():
        if isinstance(value, dict) and isinstance(merged.get(key), dict):
            merged[key] = merge_dict(merged[key], value)
        else:
            merged[key] = value
    return merged
