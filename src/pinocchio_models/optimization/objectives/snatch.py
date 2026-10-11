"""Snatch optimization objective.

Phases, timing and via-poses come from the vendored exercise spec
(standard v2.0, see :mod:`spec_lifts`).
"""

from pinocchio_models.optimization.objectives.spec_lifts import lift_objective

SNATCH_OBJECTIVE = lift_objective(
    "snatch",
    name="snatch",
    bar_path_constraint="s_curve",
    balance_mode="bilateral_stance",
)
