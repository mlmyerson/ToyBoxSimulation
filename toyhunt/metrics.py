"""Metrics helpers for Toy Hunt simulation."""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Iterable, Sequence

from .config import SummaryStats, TrialResult
from .utils import mean, stddev


@dataclass(frozen=True)
class ConfidenceInterval:
    mean: float
    lower: float
    upper: float


@dataclass(frozen=True)
class AggregateMetrics:
    summary: SummaryStats
    steps_ci: ConfidenceInterval
    wall_time_ci: ConfidenceInterval | None
    recovery_ci: ConfidenceInterval
    recovery_success_fraction: float
    bin_ratios: tuple[float, ...]
    recovery_ratios: tuple[float, ...]
    first_completion_steps: tuple[int | None, ...]
    last_completion_steps: tuple[int | None, ...]
    unfinished_areas: tuple[float, ...]
    collisions: tuple[int, ...]
    wasted_dumps: tuple[int, ...]


def _confidence_interval(values: Sequence[float]) -> ConfidenceInterval:
    if not values:
        return ConfidenceInterval(mean=0.0, lower=0.0, upper=0.0)
    m = mean(values)
    s = stddev(values)
    if len(values) <= 1 or s == 0:
        return ConfidenceInterval(mean=m, lower=m, upper=m)
    delta = 1.96 * s / math.sqrt(len(values))
    return ConfidenceInterval(mean=m, lower=m - delta, upper=m + delta)


def aggregate_trial_metrics(trial_results: Iterable[TrialResult]) -> AggregateMetrics:
    trials = list(trial_results)
    if not trials:
        raise ValueError("No trial results provided.")

    steps = [trial.steps for trial in trials]
    wall_times = [trial.wall_time for trial in trials if trial.wall_time is not None]
    unfinished_areas = [trial.unfinished_area for trial in trials]
    collisions = [trial.collisions for trial in trials]
    wasted_dumps = [trial.wasted_dumps for trial in trials]
    first_completion_steps = [trial.first_completion_step for trial in trials]
    last_completion_steps = [trial.last_completion_step for trial in trials]

    success_rate = sum(1 for trial in trials if trial.success) / len(trials)

    bin_ratios: list[float] = []
    for trial in trials:
        total_toys = max(1, trial.config.total_toys)
        bin_ratios.extend(snapshot.initial_count / total_toys for snapshot in trial.bins)

    recovery_ratios: list[float] = []
    recovery_success_count = 0
    for trial in trials:
        for child in trial.children:
            ratio = child.recovery_ratio if child.needed else 1.0
            recovery_ratios.append(ratio)
            if math.isclose(ratio, 1.0, abs_tol=1e-9):
                recovery_success_count += 1

    recovery_success_fraction = (
        recovery_success_count / len(recovery_ratios) if recovery_ratios else 0.0
    )

    summary = SummaryStats(
        trials=len(trials),
        success_rate=success_rate,
        mean_steps=mean(steps),
        step_std=stddev(steps),
        mean_wall_time=mean(wall_times) if wall_times else None,
        wall_time_std=stddev(wall_times) if len(wall_times) > 1 else None,
        mean_recovery=mean(recovery_ratios) if recovery_ratios else 0.0,
        recovery_std=stddev(recovery_ratios) if len(recovery_ratios) > 1 else 0.0,
        recovery_success_fraction=recovery_success_fraction,
        mean_bin_ratio=mean(bin_ratios) if bin_ratios else 0.0,
        bin_ratio_std=stddev(bin_ratios) if len(bin_ratios) > 1 else 0.0,
        mean_first_completion=(
            mean([step for step in first_completion_steps if step is not None])
            if any(step is not None for step in first_completion_steps)
            else None
        ),
        first_completion_std=(
            stddev([step for step in first_completion_steps if step is not None])
            if len([step for step in first_completion_steps if step is not None]) > 1
            else None
        ),
        mean_last_completion=(
            mean([step for step in last_completion_steps if step is not None])
            if any(step is not None for step in last_completion_steps)
            else None
        ),
        last_completion_std=(
            stddev([step for step in last_completion_steps if step is not None])
            if len([step for step in last_completion_steps if step is not None]) > 1
            else None
        ),
        mean_unfinished_area=mean(unfinished_areas),
        unfinished_area_std=stddev(unfinished_areas) if len(unfinished_areas) > 1 else 0.0,
        mean_collisions=mean(collisions) if collisions else 0.0,
        collision_std=stddev(collisions) if len(collisions) > 1 else 0.0,
        mean_wasted_dumps=mean(wasted_dumps) if wasted_dumps else 0.0,
        wasted_dumps_std=stddev(wasted_dumps) if len(wasted_dumps) > 1 else 0.0,
    )

    return AggregateMetrics(
        summary=summary,
        steps_ci=_confidence_interval(steps),
        wall_time_ci=_confidence_interval(wall_times) if wall_times else None,
        recovery_ci=_confidence_interval(recovery_ratios) if recovery_ratios else ConfidenceInterval(0.0, 0.0, 0.0),
        recovery_success_fraction=recovery_success_fraction,
        bin_ratios=tuple(bin_ratios),
        recovery_ratios=tuple(recovery_ratios),
        first_completion_steps=tuple(first_completion_steps),
        last_completion_steps=tuple(last_completion_steps),
        unfinished_areas=tuple(unfinished_areas),
        collisions=tuple(collisions),
        wasted_dumps=tuple(wasted_dumps),
    )
