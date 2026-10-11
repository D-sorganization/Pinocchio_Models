"""Clean and jerk optimization objective.

Phases, timing and via-poses come from the vendored exercise spec
(standard v2.0, see :mod:`spec_lifts`).
"""

from pinocchio_models.optimization.objectives.spec_lifts import lift_objective

CLEAN_AND_JERK_OBJECTIVE = lift_objective(
    "clean_and_jerk",
    name="clean_and_jerk",
    bar_path_constraint="s_curve",
    balance_mode="split_stance",
)
