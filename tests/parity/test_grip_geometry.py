"""Real-Pinocchio grip-geometry checks for barbell exercises (issue #443).

At the neutral pose the standing hands sat at shoulder width (~0.168 m) while
the grip offset was 0.3+ x shaft length (~0.39 m or wider): the bar, welded
to ``hand_l`` only, was not centred on the pelvis midline, and the right grip
existed only as a virtual anchor the right hand never reached. Since LIFT-3
(UpstreamDrift#11743) the start pose is the spec ``start`` via-pose and the
weld places the bar at the spec bar position, so both palm centres (the
standard's grip point, Repository_Management#2060) sit on the shaft at the
spec grip width with the bar centred on the midline.

Pinocchio is a ``dev`` dependency and runs in default CI (see
``test_forward_kinematics.py``, issue #428).
"""

from __future__ import annotations

import numpy as np
import pinocchio as pin
import pytest

from pinocchio_models.exercises.bench_press.bench_press_model import (
    BenchPressModelBuilder,
)
from pinocchio_models.exercises.clean_and_jerk.clean_and_jerk_model import (
    CleanAndJerkModelBuilder,
)
from pinocchio_models.exercises.deadlift.deadlift_model import DeadliftModelBuilder
from pinocchio_models.exercises.snatch.snatch_model import SnatchModelBuilder
from pinocchio_models.exercises.spec_lift import SpecLiftBuilder
from pinocchio_models.shared.parity._canonical import conformance, topology
from pinocchio_models.shared.parity.fingerprint import load_model
from pinocchio_models.shared.utils.urdf_helpers import get_initial_configuration

# Acceptance tolerance from issue #443: 1 cm. Never loosen this.
_TOLERANCE_M = 0.01

_GRIP_BUILDERS: list[tuple[str, type[SpecLiftBuilder]]] = [
    ("bench_press", BenchPressModelBuilder),
    ("deadlift", DeadliftModelBuilder),
    ("snatch", SnatchModelBuilder),
    ("clean_and_jerk", CleanAndJerkModelBuilder),
]


def _frame_translation(model: pin.Model, data: pin.Data, name: str) -> np.ndarray:
    return data.oMf[model.getFrameId(name)].translation


def _frame_placement(model: pin.Model, data: pin.Data, name: str) -> pin.SE3:
    return data.oMf[model.getFrameId(name)]


def _palm_centre(model: pin.Model, data: pin.Data, side: str) -> np.ndarray:
    """The standard's grip point: palm centre on the hand segment's z axis."""
    std = conformance.load_standard()
    factor, term = std["grip_point"]["origin"]["z"]
    hand = _frame_placement(model, data, f"hand_{side}")
    offset = np.array([0.0, 0.0, factor * topology.dimension(std, term)])
    return hand.translation + hand.rotation @ offset


@pytest.mark.parametrize(
    "name,builder_cls", _GRIP_BUILDERS, ids=[n for n, _ in _GRIP_BUILDERS]
)
def test_bar_centre_is_on_the_pelvis_midline(
    name: str, builder_cls: type[SpecLiftBuilder]
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
    name: str, builder_cls: type[SpecLiftBuilder]
) -> None:
    """Each palm centre must be within 1 cm of its grip point on the shaft.

    The grip points are +-half the spec grip width along the shaft's own
    (level) Y axis, matching the right-hand virtual anchor ``barbell_grip_r``.
    """
    builder = builder_cls()
    urdf = builder.build()
    model = load_model(urdf)
    data = model.createData()
    q0 = get_initial_configuration(model, urdf)
    pin.forwardKinematics(model, data, q0)
    pin.updateFramePlacements(model, data)

    grip_offset = builder.spec_start.grip_half_width_m
    shaft = _frame_placement(model, data, "barbell_shaft")
    left_grip_point = shaft.translation + shaft.rotation @ np.array(
        [0.0, grip_offset, 0.0]
    )
    right_grip_point = shaft.translation + shaft.rotation @ np.array(
        [0.0, -grip_offset, 0.0]
    )

    hand_l = _palm_centre(model, data, "l")
    hand_r = _palm_centre(model, data, "r")

    left_gap = float(np.linalg.norm(hand_l - left_grip_point))
    right_gap = float(np.linalg.norm(hand_r - right_grip_point))

    assert left_gap < _TOLERANCE_M, (
        f"{name}: palm l is {left_gap * 100:.2f} cm from its grip point"
    )
    assert right_gap < _TOLERANCE_M, (
        f"{name}: palm r is {right_gap * 100:.2f} cm from its grip point"
    )
