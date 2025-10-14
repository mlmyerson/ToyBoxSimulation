"""Command-line entry point for the Toy Hunt simulation."""
from __future__ import annotations

import argparse
import sys
from typing import Sequence

import numpy as np

from toyhunt.config import (
	RunOutputs,
	SimulationConfig,
	build_config,
	config_warnings,
)
from toyhunt.metrics import aggregate_trial_metrics
from toyhunt.reporting import save_outputs
from toyhunt.simulation import run_simulation


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
	parser = argparse.ArgumentParser(
		prog="toyhunt",
		description="Simulate children searching bins for their target toys.",
	)
	parser.add_argument("--bins", type=int, default=10, help="Number of bins available.")
	parser.add_argument(
		"--children",
		type=int,
		default=5,
		help="Number of children participating in the search.",
	)
	parser.add_argument(
		"--targets-per-child",
		type=int,
		default=3,
		help="Number of target toys each child needs to find.",
	)
	parser.add_argument(
		"--total-toys",
		type=int,
		default=200,
		help="Total number of toys distributed across all bins.",
	)
	parser.add_argument(
		"--bin-dist",
		choices=["even", "random"],
		default="random",
		help="Distribution policy for filling bins with toys.",
	)
	parser.add_argument(
		"--target-fraction",
		type=float,
		default=0.2,
		help="Fraction of total toys that are targetable.",
	)
	parser.add_argument(
		"--tagging",
		choices=["exclusive", "overlap"],
		default="overlap",
		help="Ownership tagging mode for targetable toys.",
	)
	parser.add_argument(
		"--bin-policy",
		choices=["random", "roundrobin"],
		default="random",
		help="Bin selection policy during the search loop.",
	)
	parser.add_argument(
		"--overlap-p",
		type=float,
		default=0.2,
		help="Probability a target toy is shared with each child in overlap mode.",
	)
	parser.add_argument(
		"--timed",
		action="store_true",
		help="Measure wall-clock runtime instead of counting steps.",
	)
	parser.add_argument(
		"--trials",
		type=int,
		default=1,
		help="Number of independent trials to run.",
	)
	parser.add_argument(
		"--seed",
		type=int,
		default=None,
		help="Random seed for reproducibility.",
	)
	parser.add_argument(
		"--plots",
		choices=["on", "off"],
		default="on",
		help="Toggle generation of plot artifacts.",
	)
	parser.add_argument(
		"--out",
		type=str,
		default="results/run_001",
		help="Directory to write results into.",
	)
	return parser.parse_args(args=argv)


def run(argv: Sequence[str] | None = None) -> RunOutputs:
	args = parse_args(argv)
	config = build_config(args)

	for warning in config_warnings(config):
		print(f"Warning: {warning}", file=sys.stderr)

	master_seed = config.seed if config.seed is not None else np.random.SeedSequence().entropy
	seed_sequence = np.random.SeedSequence(master_seed)
	child_sequences = seed_sequence.spawn(config.trials)

	trials = []
	for trial_index, seq in enumerate(child_sequences):
		trial_rng = np.random.default_rng(seq)
		trial_seed = seq.entropy
		trial_result = run_simulation(config, rng=trial_rng, seed=trial_seed)
		trials.append(trial_result)

	metrics = aggregate_trial_metrics(trials)
	outputs = save_outputs(config, trials, metrics)
	return outputs


def main() -> None:
	run()


if __name__ == "__main__":
	main()