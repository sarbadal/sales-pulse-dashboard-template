from __future__ import annotations


def to_float(value: str) -> float:
    return float(value.strip() or 0)


def to_int(value: str) -> int:
    return int(float(value.strip() or 0))
