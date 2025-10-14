# Toy Hunt Simulation

Simulate a group of children dumping bins in search of their target toys. The project provides a configurable agent-based simulation, aggregate metrics, structured artifacts (JSON + CSV), and visualizations that help explore how bin composition, toy targeting rules, and search policies influence outcomes.

## Features

- **Configurable scenario**: control bin fill strategies, tagging modes (exclusive vs. overlap), target fractions, selection policies, and reproducibility via seeds.
- **Agent-based simulation**: each child searches until their personal target quota is met or bins are exhausted, tracking collisions and wasted effort along the way.
- **Rich metrics**: confidence intervals, recovery ratios, completion timing, effort proxies, and sanity warnings when configurations are infeasible.
- **Structured outputs**: machine-readable JSON summary plus `bins.csv`, `children.csv`, and `timeline.csv` for downstream analysis.
- **Visualizations**: histogram of bin fill ratios, recovery curves with uncertainty bands, per-child completion violin, and trial outcome breakdowns.
- **Tested codebase**: pytest suite covering the simulation core, aggregation, reporting, and plotting.

## Installation

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

The requirements file includes `numpy`, `matplotlib`, and `pytest`. Additional packages are not required.

## Command-line interface

Run the simulation via `main.py` or install the package and invoke the `toyhunt` module.

```bash
python main.py \
  --bins 10 \
  --children 5 \
  --targets-per-child 3 \
  --total-toys 200 \
  --bin-dist random \
  --target-fraction 0.2 \
  --tagging overlap \
  --bin-policy random \
  --overlap-p 0.2 \
  --timed \
  --trials 5 \
  --seed 42 \
  --plots on \
  --out results/run_001
```

### Key parameters

| Flag | Description | Default |
| ---- | ----------- | ------- |
| `--bins` | Number of bins in the room. | 10 |
| `--children` | Number of children searching. | 5 |
| `--targets-per-child` | Per-child target quota (`n`). | 3 |
| `--total-toys` | Total toys distributed across bins (`T`). | 200 |
| `--bin-dist` | Bin fill strategy: `even` or `random`. | `random` |
| `--target-fraction` | Fraction of total toys that are targetable (`f`). | 0.2 |
| `--tagging` | Tagging mode: `exclusive` (one owner) or `overlap` (shared tags). | `overlap` |
| `--bin-policy` | Bin selection policy: `random` (shuffle once) or `roundrobin`. | `random` |
| `--overlap-p` | In overlap mode, probability a toy is tagged for each child. | 0.2 |
| `--timed` | Measure wall-clock time instead of dump count. | `False` |
| `--trials` | Number of independent trials to run. | 1 |
| `--seed` | Master RNG seed for reproducibility. | `None` |
| `--plots` | Toggle plot generation (`on`/`off`). | `on` |
| `--out` | Output directory for artifacts. | `results/run_001` |

### Sanity warnings

- **Exclusive mode**: if `children * targets_per_child > targetable_toys`, the run warns that full success is impossible.
- **Overlap mode**: zero targetable toys or very low overlap probability trigger warnings about expected low recovery.
- **Zero targets per child**: the simulation short-circuits with zero steps and reports immediate completion.

## Simulation flow

1. **Initialisation**
   - Allocate toys to bins using `even` or multinomial `random` distribution.
   - Mark `f * T` toys as targetable; tag them according to `exclusive` (single owner) or `overlap` (shared) rules.
   - Spawn a seeded NumPy generator for each requested trial.

2. **Search loop**
   - Select bins according to the bin policy (random shuffle or deterministic round-robin).
   - Dump the bin, expose all toys, and let each child collect any outstanding tags.
   - Track collisions (shared toys satisfying multiple children) and wasted dumps (no new targets recovered).
   - Terminate when every child meets its quota or all bins have been emptied.

3. **Metric capture**
   - Record per-step unfinished children, cumulative targets found, and resulting recovery fraction.
   - Capture steps to first and last completions, area under the unfinished curve, and trial success flag.

## Outputs

All artifacts are written to the directory supplied via `--out` (created automatically).

- `summary.json` – Echoes parameters, derived totals, summary statistics, and confidence intervals.
- `bins.csv` – One row per trial/bin with initial and target counts.
- `children.csv` – Per-trial child outcomes, including recovery ratios and completion steps.
- `timeline.csv` – Step-by-step dump timeline with unfinished counts and recovery progress.
- `*.png` plots – Histogram, recovery curve, completion violin, and success bar (when plots are enabled).

A concise human-readable summary is also printed to stdout after each run.

## Metrics overview

- **Success rate**: fraction of trials where every child met their quota.
- **Steps / wall time**: average steps (or seconds when `--timed`) with 95% confidence intervals.
- **Recovery ratio**: mean ± σ of `targets_found / needed` across all children, plus the success fraction `Pr(q_j = 1)`.
- **Bin ratio stats**: mean ± σ of `(toys_in_bin / T)` across all bins and trials.
- **Completion timing**: means & spreads for first and last child completion steps.
- **Effort proxy**: area under the unfinished-children curve.
- **Collisions & wasted dumps**: average counts per trial for overlap contention and empty dumps.

## Development

### Run tests

```bash
python -m pytest
```

### Code layout

- `main.py` – CLI entry point.
- `toyhunt/config.py` – Configuration dataclasses, validation, and helpers.
- `toyhunt/simulation.py` – Core simulation engine and trial execution.
- `toyhunt/metrics.py` – Aggregation, summary statistics, and confidence intervals.
- `toyhunt/reporting.py` – Artifact generation (JSON, CSV, console) and orchestration.
- `toyhunt/plotting.py` – Matplotlib visualizations.
- `tests/` – Pytest suite covering major functional areas.

## Reproducibility tips

- Provide `--seed` to obtain deterministic trial spawning (the seed is echoed to outputs).
- Use `--trials K` to smooth stochastic variance and inspect confidence intervals.
- Toggle `--plots off` when running in headless or batch environments to skip PNG creation.

## Next steps

- Extend the simulation with alternative bin policies (e.g., adaptive heuristics).
- Add CLI switches for optional metrics such as overlap collision severity.
- Integrate a simple web dashboard to explore results interactively.
