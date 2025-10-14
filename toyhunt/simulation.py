"""Simulation engine for the Toy Hunt experiment."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

from .config import (
    BinSnapshot,
    ChildOutcome,
    SimulationConfig,
    TimelineEntry,
    TrialResult,
)


@dataclass
class ChildState:
    child_id: int
    needed: int
    available: int
    targets: set[int]
    found: int = 0
    steps_to_finish: int | None = None

    def mark_found(self, toy_id: int, step: int) -> bool:
        if toy_id not in self.targets:
            return False
        self.targets.remove(toy_id)
        if self.found < self.needed:
            self.found += 1
        if self.found >= self.needed and self.steps_to_finish is None:
            self.steps_to_finish = step
        return True

    @property
    def done(self) -> bool:
        return self.found >= self.needed


def _allocate_bins(config: SimulationConfig, rng: np.random.Generator) -> list[int]:
    if config.bin_distribution == "even":
        base = config.total_toys // config.bins
        remainder = config.total_toys % config.bins
        return [base + (1 if i < remainder else 0) for i in range(config.bins)]
    probabilities = np.full(config.bins, 1.0 / config.bins)
    return rng.multinomial(config.total_toys, probabilities).tolist()


def _select_targetable(config: SimulationConfig, rng: np.random.Generator) -> set[int]:
    targetable = min(config.targetable_toys, config.total_toys)
    if targetable <= 0:
        return set()
    toy_ids = np.arange(config.total_toys)
    selection = rng.choice(toy_ids, size=targetable, replace=False)
    return set(int(x) for x in selection)


def _assign_tags(
    config: SimulationConfig,
    rng: np.random.Generator,
    targetable_ids: Iterable[int],
) -> tuple[dict[int, tuple[int, ...]], list[set[int]]]:
    target_map: dict[int, tuple[int, ...]] = {}
    child_targets = [set() for _ in range(config.children)]

    target_list = list(targetable_ids)
    rng.shuffle(target_list)

    if config.tagging_mode == "exclusive":
        per_child_quota = config.targets_per_child
        index = 0
        for child_id in range(config.children):
            quota = min(per_child_quota, len(target_list) - index)
            for offset in range(quota):
                toy_id = target_list[index + offset]
                target_map[toy_id] = (child_id,)
                child_targets[child_id].add(toy_id)
            index += quota
        # Assign any remaining targetable toys to random children to satisfy exclusivity.
        for toy_id in target_list[index:]:
            child_id = int(rng.integers(0, config.children))
            target_map[toy_id] = (child_id,)
            child_targets[child_id].add(toy_id)
    else:  # overlap mode
        for toy_id in target_list:
            mask = rng.random(config.children) < config.overlap_probability
            owner_ids = np.nonzero(mask)[0].tolist()
            if not owner_ids:
                owner_ids = [int(rng.integers(0, config.children))]
            owners = tuple(int(i) for i in owner_ids)
            target_map[toy_id] = owners
            for owner in owners:
                child_targets[owner].add(toy_id)

    return target_map, child_targets


def run_simulation(config: SimulationConfig, *, rng: np.random.Generator, seed: int) -> TrialResult:
    """Execute a single simulation trial."""

    bin_counts = _allocate_bins(config, rng)
    targetable_ids = _select_targetable(config, rng)
    target_map, child_targets = _assign_tags(config, rng, targetable_ids)

    bin_contents: list[list[int]] = []
    current_toy = 0
    bin_snapshots: list[BinSnapshot] = []

    for bin_id, count in enumerate(bin_counts):
        contents = list(range(current_toy, current_toy + count))
        bin_contents.append(contents)
        target_count = sum(1 for toy_id in contents if toy_id in targetable_ids)
        bin_snapshots.append(
            BinSnapshot(
                bin_id=bin_id,
                initial_count=count,
                target_count=target_count,
            )
        )
        current_toy += count

    child_states = [
        ChildState(
            child_id=i,
            needed=config.targets_per_child,
            available=len(child_targets[i]),
            targets=set(child_targets[i]),
        )
        for i in range(config.children)
    ]

    total_needed = sum(state.needed for state in child_states)

    step_order = list(range(config.bins))
    if config.bin_policy == "random":
        rng.shuffle(step_order)

    timeline: list[TimelineEntry] = []
    collisions = 0
    wasted_dumps = 0
    unfinished_area = 0.0
    first_completion_step: int | None = None
    last_completion_step: int | None = None

    if config.timed:
        import time

        start_time = time.perf_counter()
    else:
        start_time = None

    steps = 0

    for index, bin_id in enumerate(step_order, start=1):
        if all(child.done for child in child_states):
            break

        prev_unfinished = sum(1 for child in child_states if not child.done)

        toys = bin_contents[bin_id]
        wasted = True
        for toy_id in list(toys):
            owners = target_map.get(toy_id)
            if not owners:
                continue
            satisfied_children = []
            for owner in owners:
                child_state = child_states[owner]
                if child_state.mark_found(toy_id, index):
                    satisfied_children.append(owner)
            if satisfied_children:
                wasted = False
                if len(satisfied_children) > 1:
                    collisions += 1
        # Bin is emptied after dump regardless of outcome.
        bin_contents[bin_id] = []

        if wasted:
            wasted_dumps += 1

        unfinished = sum(1 for child in child_states if not child.done)
        unfinished_area += unfinished

        if first_completion_step is None and unfinished < prev_unfinished:
            first_completion_step = index
        if unfinished == 0:
            last_completion_step = index

        total_found = sum(child.found for child in child_states)
        recovery_fraction = (total_found / total_needed) if total_needed else 1.0

        timeline.append(
            TimelineEntry(
                step=index,
                dumps=index,
                unfinished_children=unfinished,
                targets_found=total_found,
                recovery_fraction=recovery_fraction,
            )
        )
        steps = index

    if config.timed and start_time is not None:
        import time

        wall_time = time.perf_counter() - start_time
    else:
        wall_time = None

    success = all(child.done for child in child_states)

    if success:
        if first_completion_step is None:
            first_completion_step = 0
        if last_completion_step is None:
            last_completion_step = steps

    child_outcomes = [
        ChildOutcome(
            child_id=state.child_id,
            found=state.found,
            needed=state.needed,
            available=state.available,
            steps_to_finish=state.steps_to_finish,
        )
        for state in child_states
    ]

    return TrialResult(
        config=config,
        seed=seed,
        success=success,
        steps=steps,
        wall_time=wall_time,
        first_completion_step=first_completion_step,
        last_completion_step=last_completion_step,
        unfinished_area=unfinished_area,
        collisions=collisions,
        wasted_dumps=wasted_dumps,
        bins=bin_snapshots,
        children=child_outcomes,
        timeline=timeline,
    )
