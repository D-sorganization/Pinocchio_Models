"""Profile representative exercise model generation paths."""

from __future__ import annotations

import builtins
from collections.abc import Callable
from typing import cast

from pinocchio_models.exercises.bench_press.bench_press_model import (
    build_bench_press_model,
)
from pinocchio_models.exercises.clean_and_jerk.clean_and_jerk_model import (
    build_clean_and_jerk_model,
)
from pinocchio_models.exercises.deadlift.deadlift_model import build_deadlift_model
from pinocchio_models.exercises.snatch.snatch_model import build_snatch_model
from pinocchio_models.exercises.squat.squat_model import build_squat_model

ModelBuilder = Callable[[], object]
ProfileTarget = Callable[[str, ModelBuilder], None]

_BUILDERS: tuple[tuple[str, ModelBuilder], ...] = (
    ("squat", build_squat_model),
    ("bench_press", build_bench_press_model),
    ("deadlift", build_deadlift_model),
    ("snatch", build_snatch_model),
    ("clean_and_jerk", build_clean_and_jerk_model),
)


def _identity_profile(func: ProfileTarget) -> ProfileTarget:
    return func


_PROFILE = cast(
    Callable[[ProfileTarget], ProfileTarget],
    getattr(builtins, "profile", _identity_profile),
)


@_PROFILE
def _profiled_build(name: str, build_model: ModelBuilder) -> None:
    model = build_model()
    if model is None:
        msg = f"{name} builder returned None"
        raise RuntimeError(msg)


def _run_profile(iterations: int = 1) -> None:
    """Build representative models enough times to produce useful profiler output."""
    if iterations < 1:
        msg = "iterations must be at least 1"
        raise ValueError(msg)

    for name, build_model in _BUILDERS:
        for _ in range(iterations):
            _profiled_build(name, build_model)
        print(f"profiled {name} generation")


def _main() -> None:
    """Run the model generation profiling workload."""
    _run_profile()


if __name__ == "__main__":
    _main()
