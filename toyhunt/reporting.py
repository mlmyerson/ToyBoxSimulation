"""Reporting utilities for Toy Hunt simulation."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Sequence

from .config import SimulationConfig, TrialResult
from .metrics import AggregateMetrics, ConfidenceInterval
from .plotting import generate_plots


@dataclass(frozen=True)
class RunOutputs:
    metrics: AggregateMetrics
    output_dir: Path
    summary_path: Path
    bin_csv_path: Path
    children_csv_path: Path
    timeline_csv_path: Path
    plot_paths: Sequence[Path]


def _ci_to_dict(ci: ConfidenceInterval | None) -> dict[str, float] | None:
    if ci is None:
        return None
    return {"mean": ci.mean, "lower": ci.lower, "upper": ci.upper}


def _write_summary_json(
    config: SimulationConfig,
    metrics: AggregateMetrics,
    summary_path: Path,
) -> None:
    summary_data = {
        "parameters": {
            "bins": config.bins,
            "children": config.children,
            "targets_per_child": config.targets_per_child,
            "total_toys": config.total_toys,
            "bin_distribution": config.bin_distribution,
            "target_fraction": config.target_fraction,
            "tagging_mode": config.tagging_mode,
            "bin_policy": config.bin_policy,
            "overlap_probability": config.overlap_probability,
            "timed": config.timed,
            "trials": config.trials,
            "seed": config.seed,
            "targetable_toys": config.targetable_toys,
            "required_targets": config.required_targets,
        },
        "metrics": {
            "success_rate": metrics.summary.success_rate,
            "mean_steps": metrics.summary.mean_steps,
            "step_std": metrics.summary.step_std,
            "steps_ci": _ci_to_dict(metrics.steps_ci),
            "mean_wall_time": metrics.summary.mean_wall_time,
            "wall_time_std": metrics.summary.wall_time_std,
            "wall_time_ci": _ci_to_dict(metrics.wall_time_ci),
            "mean_recovery": metrics.summary.mean_recovery,
            "recovery_std": metrics.summary.recovery_std,
            "recovery_ci": _ci_to_dict(metrics.recovery_ci),
            "recovery_success_fraction": metrics.summary.recovery_success_fraction,
            "mean_bin_ratio": metrics.summary.mean_bin_ratio,
            "bin_ratio_std": metrics.summary.bin_ratio_std,
            "mean_first_completion": metrics.summary.mean_first_completion,
            "first_completion_std": metrics.summary.first_completion_std,
            "mean_last_completion": metrics.summary.mean_last_completion,
            "last_completion_std": metrics.summary.last_completion_std,
            "mean_unfinished_area": metrics.summary.mean_unfinished_area,
            "unfinished_area_std": metrics.summary.unfinished_area_std,
            "mean_collisions": metrics.summary.mean_collisions,
            "collision_std": metrics.summary.collision_std,
            "mean_wasted_dumps": metrics.summary.mean_wasted_dumps,
            "wasted_dumps_std": metrics.summary.wasted_dumps_std,
        },
    }

    summary_path.write_text(json.dumps(summary_data, indent=2))


def _write_bins_csv(path: Path, trials: Sequence[TrialResult]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["trial", "bin_id", "initial_count", "target_count"])
        for trial_index, trial in enumerate(trials, start=1):
            for snapshot in trial.bins:
                writer.writerow(
                    [
                        trial_index,
                        snapshot.bin_id,
                        snapshot.initial_count,
                        snapshot.target_count,
                    ]
                )


def _write_children_csv(path: Path, trials: Sequence[TrialResult]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "trial",
                "child_id",
                "found",
                "needed",
                "available",
                "steps_to_finish",
                "recovery_ratio",
            ]
        )
        for trial_index, trial in enumerate(trials, start=1):
            for outcome in trial.children:
                writer.writerow(
                    [
                        trial_index,
                        outcome.child_id,
                        outcome.found,
                        outcome.needed,
                        outcome.available,
                        outcome.steps_to_finish if outcome.steps_to_finish is not None else "",
                        f"{outcome.recovery_ratio:.3f}",
                    ]
                )


def _write_timeline_csv(path: Path, trials: Sequence[TrialResult]) -> None:
    with path.open("w", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(
            [
                "trial",
                "step",
                "dumps",
                "unfinished_children",
                "targets_found",
                "recovery_fraction",
            ]
        )
        for trial_index, trial in enumerate(trials, start=1):
            for entry in trial.timeline:
                writer.writerow(
                    [
                        trial_index,
                        entry.step,
                        entry.dumps,
                        entry.unfinished_children,
                        entry.targets_found,
                        f"{entry.recovery_fraction:.3f}",
                    ]
                )


def _format_summary_table(config: SimulationConfig, metrics: AggregateMetrics) -> str:
    lines = [
        "=== Toy Hunt Summary ===",
        f"Trials: {metrics.summary.trials}",
        f"Success rate: {metrics.summary.success_rate:.2%}",
        f"Mean steps: {metrics.summary.mean_steps:.2f} ± {metrics.summary.step_std:.2f}",
    ]
    if metrics.summary.mean_wall_time is not None:
        wall_std = metrics.summary.wall_time_std if metrics.summary.wall_time_std is not None else 0.0
        lines.append(
            f"Mean wall time: {metrics.summary.mean_wall_time:.3f}s ± {wall_std:.3f}s"
        )
    lines.extend(
        [
            f"Mean recovery ratio: {metrics.summary.mean_recovery:.3f} (σ={metrics.summary.recovery_std:.3f})",
            f"Child success rate: {metrics.summary.recovery_success_fraction:.2%}",
            f"Mean bin fill ratio: {metrics.summary.mean_bin_ratio:.3f} (σ={metrics.summary.bin_ratio_std:.3f})",
            f"Mean unfinished area: {metrics.summary.mean_unfinished_area:.2f}",
            f"Mean collisions: {metrics.summary.mean_collisions:.2f}",
            f"Mean wasted dumps: {metrics.summary.mean_wasted_dumps:.2f}",
        ]
    )
    if metrics.summary.mean_first_completion is not None:
        first_std = (
            metrics.summary.first_completion_std if metrics.summary.first_completion_std is not None else 0.0
        )
        lines.append(
            f"First completion (mean): {metrics.summary.mean_first_completion:.2f} ± {first_std:.2f} steps"
        )
    if metrics.summary.mean_last_completion is not None:
        last_std = (
            metrics.summary.last_completion_std if metrics.summary.last_completion_std is not None else 0.0
        )
        lines.append(
            f"Last completion (mean): {metrics.summary.mean_last_completion:.2f} ± {last_std:.2f} steps"
        )
    lines.append(f"Output directory: {config.output_dir}")
    return "\n".join(lines)


def save_outputs(
    config: SimulationConfig,
    trials: Iterable[TrialResult],
    metrics: AggregateMetrics,
) -> RunOutputs:
    trials_list = list(trials)
    output_dir = config.output_dir
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_path = output_dir / "summary.json"
    bins_path = output_dir / "bins.csv"
    children_path = output_dir / "children.csv"
    timeline_path = output_dir / "timeline.csv"

    _write_summary_json(config, metrics, summary_path)
    _write_bins_csv(bins_path, trials_list)
    _write_children_csv(children_path, trials_list)
    _write_timeline_csv(timeline_path, trials_list)

    print(_format_summary_table(config, metrics))

    plot_paths: list[Path] = []
    if config.plots.enabled:
        plot_paths = list(generate_plots(trials_list, output_dir))

    return RunOutputs(
        metrics=metrics,
        output_dir=output_dir,
        summary_path=summary_path,
        bin_csv_path=bins_path,
        children_csv_path=children_path,
        timeline_csv_path=timeline_path,
        plot_paths=tuple(plot_paths),
    )
