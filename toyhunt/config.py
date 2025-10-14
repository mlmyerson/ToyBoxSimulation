"""Configuration models, CLI parsing, and validation for Toy Hunt simulation."""
from __future__ import annotations

from argparse import Namespace
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Literal, Optional, Sequence


BinDistribution = Literal["even", "random"]
TaggingMode = Literal["exclusive", "overlap"]
BinPolicy = Literal["random", "roundrobin"]


@dataclass(frozen=True)
class PlotConfig:
    """Plotting-related configuration."""

    enabled: bool = True
    output_dir: Path | None = None


@dataclass(frozen=True)
class SimulationConfig:
    """Complete configuration for a Toy Hunt simulation run."""

    bins: int
    children: int
    targets_per_child: int
    total_toys: int
    bin_distribution: BinDistribution
    target_fraction: float
    tagging_mode: TaggingMode
    bin_policy: BinPolicy
    overlap_probability: float
    timed: bool
    trials: int
    seed: Optional[int]
    output_dir: Path
    plots: PlotConfig

    @property
    def required_targets(self) -> int:
        return self.children * self.targets_per_child

    @property
    def targetable_toys(self) -> int:
        return int(round(self.total_toys * self.target_fraction))


@dataclass(frozen=True)
class BinSnapshot:
    """Static information about a bin at simulation start."""

    bin_id: int
    initial_count: int
    target_count: int


@dataclass(frozen=True)
class ChildOutcome:
    """Outcome metrics tracked per child."""

    child_id: int
    found: int
    needed: int
    available: int
    steps_to_finish: Optional[int]

    @property
    def recovery_ratio(self) -> float:
        return (self.found / self.needed) if self.needed else 1.0


@dataclass(frozen=True)
class TimelineEntry:
    """Timeline metrics captured per dump step."""

    step: int
    dumps: int
    unfinished_children: int
    targets_found: int
    recovery_fraction: float


@dataclass(frozen=True)
class TrialResult:
    """Complete record of a single simulation trial."""

    config: SimulationConfig
    seed: int
    success: bool
    steps: int
    wall_time: float | None
    first_completion_step: Optional[int]
    last_completion_step: Optional[int]
    unfinished_area: float
    collisions: int
    wasted_dumps: int
    bins: Sequence[BinSnapshot]
    children: Sequence[ChildOutcome]
    timeline: Sequence[TimelineEntry]


@dataclass(frozen=True)
class SummaryStats:
    """Aggregated statistics across trials."""

    trials: int
    success_rate: float
    mean_steps: float
    step_std: float
    mean_wall_time: Optional[float]
    wall_time_std: Optional[float]
    mean_recovery: float
    recovery_std: float
    recovery_success_fraction: float
    mean_bin_ratio: float
    bin_ratio_std: float
    mean_first_completion: Optional[float]
    first_completion_std: Optional[float]
    mean_last_completion: Optional[float]
    last_completion_std: Optional[float]
    mean_unfinished_area: float
    unfinished_area_std: float
    mean_collisions: float
    collision_std: float
    mean_wasted_dumps: float
    wasted_dumps_std: float


class ConfigurationError(ValueError):
    """Raised when CLI inputs are invalid."""


def validate_config(config: SimulationConfig) -> None:
    """Validate configuration fields and raise :class:`ConfigurationError` on issues."""

    if config.bins <= 0:
        raise ConfigurationError("--bins must be positive")
    if config.children <= 0:
        raise ConfigurationError("--children must be positive")
    if config.targets_per_child < 0:
        raise ConfigurationError("--targets-per-child must be non-negative")
    if config.targets_per_child == 0:
        return
    if config.total_toys <= 0:
        raise ConfigurationError("--total-toys must be positive")
    if not (0.0 <= config.target_fraction <= 1.0):
        raise ConfigurationError("--target-fraction must be between 0 and 1")
    if config.trials <= 0:
        raise ConfigurationError("--trials must be positive")
    if config.overlap_probability < 0 or config.overlap_probability > 1:
        raise ConfigurationError("--overlap-p must be between 0 and 1")
    if config.seed is not None and config.seed < 0:
        raise ConfigurationError("--seed must be non-negative")


def config_warnings(config: SimulationConfig) -> list[str]:
    """Return user-facing warnings detected during validation."""

    warnings: list[str] = []
    if config.tagging_mode == "exclusive" and config.required_targets > config.targetable_toys:
        warnings.append(
            "Exclusive tagging cannot meet demand: required targets exceed targetable toys."
        )
    if config.tagging_mode == "overlap" and config.targetable_toys == 0:
        warnings.append(
            "Overlap tagging with zero targetable toys yields zero recovery; expect failures."
        )
    if config.targets_per_child == 0:
        warnings.append("Each child requires zero targets; simulation will complete immediately.")
    if config.target_fraction == 0:
        warnings.append("Target fraction is zero; no child will find any targets.")
    return warnings


def ensure_output_dir(path: Path) -> Path:
    path.mkdir(parents=True, exist_ok=True)
    return path


def plots_enabled(config: SimulationConfig) -> bool:
    return config.plots.enabled


def build_config(namespace: Namespace) -> SimulationConfig:
    """Construct a :class:`SimulationConfig` from an argparse namespace."""

    output_dir = ensure_output_dir(Path(namespace.out).expanduser().resolve())
    plot_dir = output_dir if namespace.plots == "on" else None

    config = SimulationConfig(
        bins=namespace.bins,
        children=namespace.children,
        targets_per_child=namespace.targets_per_child,
        total_toys=namespace.total_toys,
        bin_distribution=namespace.bin_dist,
        target_fraction=namespace.target_fraction,
        tagging_mode=namespace.tagging,
        bin_policy=namespace.bin_policy,
        overlap_probability=namespace.overlap_p,
        timed=namespace.timed,
        trials=namespace.trials,
        seed=namespace.seed,
        output_dir=output_dir,
        plots=PlotConfig(enabled=namespace.plots == "on", output_dir=plot_dir),
    )
    validate_config(config)
    return config
