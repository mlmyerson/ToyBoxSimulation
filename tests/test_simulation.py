"""Unit tests for Toy Hunt simulation suite."""
from __future__ import annotations

import numpy as np
import pytest

from toyhunt.config import PlotConfig, SimulationConfig, config_warnings
from toyhunt.metrics import aggregate_trial_metrics
from toyhunt.plotting import generate_plots
from toyhunt.reporting import save_outputs
from toyhunt.simulation import run_simulation


def _base_config(tmp_path) -> SimulationConfig:
    return SimulationConfig(
        bins=4,
        children=3,
        targets_per_child=2,
        total_toys=24,
        bin_distribution="even",
        target_fraction=0.75,
        tagging_mode="overlap",
        bin_policy="roundrobin",
        overlap_probability=0.5,
        timed=False,
        trials=3,
        seed=123,
        output_dir=tmp_path,
        plots=PlotConfig(enabled=False, output_dir=None),
    )


def test_run_simulation_success(tmp_path):
    config = _base_config(tmp_path)
    rng = np.random.default_rng(123)
    trial = run_simulation(config, rng=rng, seed=123)

    assert trial.steps <= config.bins
    assert len(trial.timeline) == trial.steps
    total_found = sum(child.found for child in trial.children)
    assert total_found >= 0
    assert trial.collisions >= 0


def test_aggregate_metrics_and_reporting(tmp_path):
    config = _base_config(tmp_path)
    seed_seq = np.random.SeedSequence(321)
    trials = []
    for child_seq in seed_seq.spawn(3):
        trial_rng = np.random.default_rng(child_seq)
        trials.append(run_simulation(config, rng=trial_rng, seed=int(child_seq.entropy)))

    metrics = aggregate_trial_metrics(trials)
    assert metrics.summary.trials == len(trials)
    assert metrics.summary.mean_steps >= 0
    assert metrics.steps_ci.mean == pytest.approx(metrics.summary.mean_steps)

    outputs = save_outputs(config, trials, metrics)
    assert outputs.summary_path.exists()
    assert outputs.bin_csv_path.exists()
    assert outputs.children_csv_path.exists()
    assert outputs.timeline_csv_path.exists()


def test_generate_plots(tmp_path):
    config = _base_config(tmp_path)
    seed_seq = np.random.SeedSequence(999)
    trials = []
    for child_seq in seed_seq.spawn(2):
        trial_rng = np.random.default_rng(child_seq)
        trials.append(run_simulation(config, rng=trial_rng, seed=int(child_seq.entropy)))

    plot_paths = list(generate_plots(trials, tmp_path))
    assert plot_paths, "Expected at least one plot to be generated"
    for path in plot_paths:
        assert path.exists()


def test_config_warnings_for_insufficient_targets(tmp_path):
    config = SimulationConfig(
        bins=2,
        children=2,
        targets_per_child=3,
        total_toys=6,
        bin_distribution="even",
        target_fraction=0.1,
        tagging_mode="exclusive",
        bin_policy="random",
        overlap_probability=0.0,
        timed=False,
        trials=1,
        seed=None,
        output_dir=tmp_path,
        plots=PlotConfig(enabled=False, output_dir=None),
    )
    warnings = config_warnings(config)
    assert any("Exclusive tagging cannot meet demand" in warning for warning in warnings)
