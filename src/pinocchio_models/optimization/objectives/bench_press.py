"""Bench press optimization objective.

Phases, timing and via-poses come from the vendored exercise spec
(standard v2.0, see :mod:`spec_lifts`).
"""

from pinocchio_models.optimization.objectives.spec_lifts import lift_objective

BENCH_PRESS_OBJECTIVE = lift_objective(
    "bench_press",
    name="bench_press",
    bar_path_constraint="j_curve",
    balance_mode="supine",
)
