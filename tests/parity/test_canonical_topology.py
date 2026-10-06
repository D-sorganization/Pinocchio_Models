"""Real-engine topology conformance (issue #435): left at +Y, standard origins."""

from __future__ import annotations

import numpy as np
import pinocchio as pin
import pytest

from pinocchio_models.__main__ import _BUILDERS
from pinocchio_models.shared.parity._canonical import conformance, topology
from pinocchio_models.shared.parity.fingerprint import (
    fingerprint,
    load_model,
)

STD = conformance.load_standard()
_CATEGORIES = ("axis.", "side.", "origin.", "pose.")


@pytest.fixture(scope="module")
def squat() -> tuple[pin.Model, pin.Data]:
    model = load_model(_BUILDERS["back_squat"](), STD)
    data = model.createData()
    pin.forwardKinematics(model, data, pin.neutral(model))
    pin.updateFramePlacements(model, data)
    return model, data


def _origin(squat: tuple[pin.Model, pin.Data], body: str) -> np.ndarray:
    model, data = squat
    return np.array(data.oMf[model.getFrameId(body)].translation)


@pytest.mark.parametrize(
    "body", ["thigh", "shank", "foot", "upper_arm", "forearm", "hand"]
)
def test_left_is_plus_y_right_is_minus_y(
    squat: tuple[pin.Model, pin.Data], body: str
) -> None:
    assert _origin(squat, f"{body}_l")[1] > 0.0 > _origin(squat, f"{body}_r")[1]


def test_origins_match_the_standard_topology(
    squat: tuple[pin.Model, pin.Data],
) -> None:
    pelvis = _origin(squat, "pelvis")
    for seg, want in topology.reference_origins(STD, {}).items():
        got = _origin(squat, seg) - pelvis
        assert got == pytest.approx(want, abs=1e-3), seg


@pytest.mark.parametrize("exercise", ["squat", "bench_press"])
def test_fingerprint_has_no_topology_divergences(exercise: str) -> None:
    fp = fingerprint(exercise)
    keys = [d.key for d in conformance.check_fingerprint(fp, STD)]
    assert [k for k in keys if k.startswith(_CATEGORIES)] == []


def test_hip_flexion_moves_the_knee_forward_not_sideways() -> None:
    model = load_model(_BUILDERS["back_squat"](), STD)
    frame = model.getFrameId("shank_l")

    def knee(angle: float) -> np.ndarray:
        data = model.createData()
        q = pin.neutral(model)
        q[model.joints[model.getJointId("hip_l_flex")].idx_q] = angle
        pin.framesForwardKinematics(model, data, q)
        return np.array(data.oMf[frame].translation)

    delta = knee(np.radians(30.0)) - knee(0.0)
    assert delta[0] > 0.0
    assert abs(delta[1]) < 1e-6


def test_bench_press_lifter_is_supine() -> None:
    model = load_model(_BUILDERS["bench_press"](), STD)
    data = model.createData()
    pin.framesForwardKinematics(model, data, pin.neutral(model))
    rot = data.oMf[model.getFrameId("pelvis")].rotation
    assert rot @ np.array([1.0, 0.0, 0.0]) == pytest.approx([0.0, 0.0, 1.0], abs=1e-6)
