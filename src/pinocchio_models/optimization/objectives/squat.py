"""Squat optimization objective.

Phases, timing and via-poses come from the vendored exercise spec
(standard v2.0, see :mod:`spec_lifts`).
"""

from pinocchio_models.optimization.objectives.spec_lifts import lift_objective

SQUAT_OBJECTIVE = lift_objective(
    "squat",
    name="back_squat",
    bar_path_constraint="vertical",
    balance_mode="bilateral_stance",
)
