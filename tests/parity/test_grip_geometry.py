"""Real-Pinocchio grip-geometry checks for barbell exercises (issue #443).

At the neutral pose the standing hands sat at shoulder width (~0.168 m) while
the grip offset was 0.3+ x shaft length (~0.39 m or wider): the bar, welded
to ``hand_l`` only, was not centred on the pelvis midline, and the right grip
existed only as a virtual anchor the right hand never reached. The fix
derives a shoulder-abduction angle from each exercise's grip width
(``canonical_topology.solve_grip_abduction``) and re-levels the barbell weld
to cancel the resulting hand-frame rotation, so both hands end up on the
shaft at the intended grip points with the bar centred on the midline.

Pinocchio is a ``dev`` dependency and runs in default CI (see
``test_forward_kinematics.py``, issue #428).
"""

from __future__ import annotations

import numpy as np
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
from pinocchio_models.shared.parity.fingerprint import load_model
from pinocchio_models.shared.utils.urdf_helpers import get_initial_configuration

# Acceptance tolerance from issue #443: 1 cm. Never loosen this.
_TOLERANCE_M = 0.01

_GRIP_BUILDERS: list[tuple[str, type[ExerciseModelBuilder]]] = [
    ("bench_press", BenchPressModelBuilder),
    ("deadlift", DeadliftModelBuilder),
    ("snatch", SnatchModelBuilder),
    ("clean_and_jerk", CleanAndJerkModelBuilder),
]


def _frame_translation(model: pin.Model, data: pin.Data, name: str) -> np.ndarray:
    return data.oMf[model.getFrameId(name)].translation


def _frame_placement(model: pin.Model, data: pin.Data, name: str) -> pin.SE3:
    return data.oMf[model.getFrameId(name)]


@pytest.mark.parametrize(
    "name,builder_cls", _GRIP_BUILDERS, ids=[n for n, _ in _GRIP_BUILDERS]
)
def test_bar_centre_is_on_the_pelvis_midline(
    name: str, builder_cls: type[ExerciseModelBuilder]
) -> None:
    """The barbell shaft's Y coordinate must be within 1 cm of y=0."""
    builder = builder_cls()
    urdf = builder.build()
    model = load_model(urdf)
    data = model.createData()
    q0 = get_initial_configuration(model, urdf)
    pin.forwardKinematics(model, data, q0)
    pin.updateFramePlacements(model, data)

    shaft_y = float(_frame_translation(model, data, "barbell_shaft")[1])
    assert abs(shaft_y) < _TOLERANCE_M, (
        f"{name}: bar centre y={shaft_y:.4f} m, expected |y| < {_TOLERANCE_M} m"
    )


@pytest.mark.parametrize(
    "name,builder_cls", _GRIP_BUILDERS, ids=[n for n, _ in _GRIP_BUILDERS]
)
def test_both_hands_are_on_their_grip_points(
    name: str, builder_cls: type[ExerciseModelBuilder]
) -> None:
    """Each hand frame must be within 1 cm of its grip point on the shaft.

    The grip points are +-grip_offset along the shaft's own (now level) Y
    axis, matching the convention already used for the right-hand virtual
    anchor in ``ExerciseModelBuilder._attach_virtual_grip_right``.
    """
    builder = builder_cls()
    urdf = builder.build()
    model = load_model(urdf)
    data = model.createData()
    q0 = get_initial_configuration(model, urdf)
    pin.forwardKinematics(model, data, q0)
    pin.updateFramePlacements(model, data)

    grip_offset = builder.barbell_spec.shaft_length * builder.grip_offset_fraction
    shaft = _frame_placement(model, data, "barbell_shaft")
    left_grip_point = shaft.translation + shaft.rotation @ np.array(
        [0.0, grip_offset, 0.0]
    )
    right_grip_point = shaft.translation + shaft.rotation @ np.array(
        [0.0, -grip_offset, 0.0]
    )

    hand_l = _frame_translation(model, data, "hand_l")
    hand_r = _frame_translation(model, data, "hand_r")

    left_gap = float(np.linalg.norm(hand_l - left_grip_point))
    right_gap = float(np.linalg.norm(hand_r - right_grip_point))

    assert left_gap < _TOLERANCE_M, (
        f"{name}: hand_l is {left_gap * 100:.2f} cm from its grip point"
    )
    assert right_gap < _TOLERANCE_M, (
        f"{name}: hand_r is {right_gap * 100:.2f} cm from its grip point"
    )
