"""Every barbell exercise's initial pose must satisfy the model's own
joint limits (issue #459, follow-up to #443).

FK ignores URDF ``<limit>`` elements, so a joint limit that is too narrow
for an exercise's start pose (e.g. the snatch's wide-grip shoulder
abduction) silently passes FK-only checks while a limit-aware consumer
(IK, optimisation, dynamics) would see an infeasible start configuration.

Pinocchio is a ``dev`` dependency and runs in default CI (see
``test_grip_geometry.py``, issue #443; ``test_engine_conformance.py``,
issue #423).
"""

from __future__ import annotations

import math

import pinocchio as pin
import pytest

from pinocchio_models.exercises.base import ExerciseModelBuilder
from pinocchio_models.exercises.bench_press.bench_press_model import (
    BenchPressModelBuilder,
)
from pinocchio_models.exercises.clean_and_jerk.clean_and_jerk_model import (
    CleanAndJerkModelBuilder,
)
from pinocchio_models.exercises.deadlift.deadlift_model import DeadliftModelBuilder
from pinocchio_models.exercises.snatch.snatch_model import SnatchModelBuilder
from pinocchio_models.exercises.squat.squat_model import SquatModelBuilder
from pinocchio_models.shared.parity.fingerprint import load_model
from pinocchio_models.shared.utils.urdf_helpers import get_initial_configuration

# Every exercise that attaches a barbell (gait and sit_to_stand are
# bodyweight and are out of scope for this check).
_BARBELL_BUILDERS: list[tuple[str, type[ExerciseModelBuilder]]] = [
    ("back_squat", SquatModelBuilder),
    ("bench_press", BenchPressModelBuilder),
    ("deadlift", DeadliftModelBuilder),
    ("snatch", SnatchModelBuilder),
    ("clean_and_jerk", CleanAndJerkModelBuilder),
]

# Pinocchio reports a free-flyer's unbounded dofs with limits near +-1e19;
# anything that large is "no limit" and must never fail this check.
_UNBOUNDED_RAD = 1.0e18


def _joint_limit_violations(
    model: pin.Model, q0: object
) -> list[tuple[str, float, float, float]]:
    """Return ``(joint_name, value, lower, upper)`` for every q0 entry
    outside its own joint's declared limits (free-flyer dofs excluded)."""
    violations: list[tuple[str, float, float, float]] = []
    for joint_id in range(1, model.njoints):
        joint = model.joints[joint_id]
        if joint.nq != 1:
            continue  # free-flyer root: unconstrained by convention
        idx_q = joint.idx_q
        lower = float(model.lowerPositionLimit[idx_q])
        upper = float(model.upperPositionLimit[idx_q])
        if abs(lower) >= _UNBOUNDED_RAD or abs(upper) >= _UNBOUNDED_RAD:
            continue
        value = float(q0[idx_q])
        if value < lower or value > upper:
            violations.append((model.names[joint_id], value, lower, upper))
    return violations


@pytest.mark.parametrize(
    "name,builder_cls", _BARBELL_BUILDERS, ids=[n for n, _ in _BARBELL_BUILDERS]
)
def test_initial_pose_within_joint_limits(
    name: str, builder_cls: type[ExerciseModelBuilder]
) -> None:
    """Every coordinate of the initial configuration must lie within the
    URDF's own declared ``<limit lower=".." upper=".."/>`` for that joint."""
    builder = builder_cls()
    urdf = builder.build()
    model = load_model(urdf)
    q0 = get_initial_configuration(model, urdf)

    violations = _joint_limit_violations(model, q0)
    assert not violations, [
        f"{name}: {joint} = {math.degrees(value):.2f} deg, "
        f"limit [{math.degrees(lower):.2f}, {math.degrees(upper):.2f}] deg"
        for joint, value, lower, upper in violations
    ]
