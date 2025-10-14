"""Utility helpers for Toy Hunt simulation."""
from __future__ import annotations

from collections.abc import Iterable
from typing import Any, Sequence


def mean(values: Iterable[float]) -> float:
    vals = list(values)
    return sum(vals) / len(vals) if vals else 0.0


def stddev(values: Iterable[float]) -> float:
    vals = list(values)
    n = len(vals)
    if n < 2:
        return 0.0
    m = mean(vals)
    return (sum((x - m) ** 2 for x in vals) / (n - 1)) ** 0.5
