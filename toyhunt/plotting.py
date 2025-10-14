"""Plotting utilities for Toy Hunt simulation."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable, Iterator, Sequence

import matplotlib.pyplot as plt
import numpy as np

from .config import TrialResult


def _save_fig(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
    return path


def _bin_histogram(trials: Sequence[TrialResult], output_dir: Path) -> Path | None:
    bin_counts = [snapshot.initial_count for trial in trials for snapshot in trial.bins]
    target_counts = [snapshot.target_count for trial in trials for snapshot in trial.bins]
    if not bin_counts:
        return None

    plt.figure(figsize=(8, 5))
    bins = max(10, int(np.sqrt(len(bin_counts))))
    plt.hist(bin_counts, bins=bins, alpha=0.6, label="Total toys")
    if any(target_counts):
        plt.hist(target_counts, bins=bins, alpha=0.6, label="Target toys")
    plt.title("Bin Composition Histogram")
    plt.xlabel("Toy count")
    plt.ylabel("Frequency")
    plt.legend()
    return _save_fig(output_dir / "bin_histogram.png")


def _recovery_curve(trials: Sequence[TrialResult], output_dir: Path) -> Path | None:
    if not trials:
        return None
    max_steps = max((len(trial.timeline) for trial in trials), default=0)
    if max_steps == 0:
        return None

    fractions = np.zeros((len(trials), max_steps))
    for idx, trial in enumerate(trials):
        last_fraction = 0.0
        for step_index in range(max_steps):
            if step_index < len(trial.timeline):
                last_fraction = trial.timeline[step_index].recovery_fraction
            fractions[idx, step_index] = last_fraction

    mean_curve = fractions.mean(axis=0)
    std_curve = fractions.std(axis=0, ddof=1) if len(trials) > 1 else np.zeros_like(mean_curve)
    steps = np.arange(1, max_steps + 1)

    plt.figure(figsize=(8, 5))
    plt.plot(steps, mean_curve, label="Mean recovery", color="tab:blue")
    plt.fill_between(
        steps,
        mean_curve - std_curve,
        mean_curve + std_curve,
        color="tab:blue",
        alpha=0.2,
        label="±1σ",
    )
    plt.ylim(0, 1.05)
    plt.xlabel("Step")
    plt.ylabel("Fraction of targets found")
    plt.title("Recovery Curve")
    plt.legend()
    return _save_fig(output_dir / "recovery_curve.png")


def _completion_violin(trials: Sequence[TrialResult], output_dir: Path) -> Path | None:
    steps_to_finish = [
        outcome.steps_to_finish
        for trial in trials
        for outcome in trial.children
        if outcome.steps_to_finish is not None
    ]
    if not steps_to_finish:
        return None

    plt.figure(figsize=(6, 5))
    plt.violinplot(steps_to_finish, showmedians=True)
    plt.title("Distribution of Completion Steps per Child")
    plt.ylabel("Steps to finish")
    plt.xticks([])
    return _save_fig(output_dir / "completion_violin.png")


def _success_rate(trials: Sequence[TrialResult], output_dir: Path) -> Path | None:
    total = len(trials)
    if total == 0:
        return None
    success = sum(1 for trial in trials if trial.success)
    failure = total - success

    plt.figure(figsize=(5, 5))
    plt.bar(["Success", "Failure"], [success, failure], color=["tab:green", "tab:red"])
    plt.title("Trial Outcomes")
    plt.ylabel("Count")
    return _save_fig(output_dir / "success_rate.png")


def generate_plots(
    trials: Iterable[TrialResult],
    output_dir: Path,
) -> Iterator[Path]:
    trials_seq = list(trials)
    plot_builders = (
        _bin_histogram,
        _recovery_curve,
        _completion_violin,
        _success_rate,
    )
    for builder in plot_builders:
        path = builder(trials_seq, output_dir)
        if path is not None:
            yield path
