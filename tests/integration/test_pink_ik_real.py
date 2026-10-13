"""Real Pink inverse-kinematics checks on a real Pinocchio model (issue #429).

The mocked tests in ``tests/unit/addons/test_pink_ik.py`` only cover
contracts and control flow. These tests drive the real ``pink`` solver on
the squat URDF and assert that frame-position and ground (foot height)
targets are met with residuals under the 1 cm acceptance bar of #429.

Targets are built by forward kinematics of a configuration that lies
inside the joint limits, so every target is reachable by construction and
a residual above the bar is a solver defect, not an infeasible request.

The module skips cleanly when ``pink`` is not installed.
"""

from __future__ import annotations

import importlib
import warnings
from types import ModuleType

import numpy as np
import pytest

pytest.importorskip("pink")
pin = pytest.importorskip("pinocchio")

from pinocchio_models.addons.pink import ik_solver, ik_solver_tasks  # noqa: E402
from pinocchio_models.addons.pink.ik_solver import IKProblem  # noqa: E402
from pinocchio_models.exceptions import GeometryError  # noqa: E402
from pinocchio_models.shared.body.foot_sole import sole_depth_m  # noqa: E402
from pinocchio_models.shared.parity.fingerprint import build_urdf  # noqa: E402

pytestmark = pytest.mark.integration

# Acceptance bar from issue #429: frame and ground residuals under 1 cm.
RESIDUAL_BAR_M = 0.01

FEET = ("foot_l", "foot_r")
BAR_FRAME = "barbell_shaft"
HAND_FRAME = "hand_l"


@pytest.fixture
def ik() -> ModuleType:
    """Return the IK facade bound to the real ``pink`` and ``pinocchio``.

    The mocked unit tests reload these modules against fake or missing
    packages and leave them that way, so reload before every test here.
    """
    importlib.reload(ik_solver_tasks)
    return importlib.reload(ik_solver)


@pytest.fixture
def problem(ik: ModuleType) -> IKProblem:
    """Squat model wrapped as an IK problem."""
    result: IKProblem = ik.create_ik_problem(build_urdf("squat"), [BAR_FRAME, *FEET])
    return result


def _set_joint(model: pin.Model, q: np.ndarray, joint: str, value: float) -> None:
    joint_id = model.getJointId(joint)
    q[model.joints[joint_id].idx_q] = value


def _frame_pose(model: pin.Model, q: np.ndarray, frame: str) -> pin.SE3:
    data = model.createData()
    pin.framesForwardKinematics(model, data, q)
    return data.oMf[model.getFrameId(frame)].copy()


def _grounded_squat_configuration(model: pin.Model) -> np.ndarray:
    """Return a within-limits squat-like configuration with soles on the ground.

    Hip flexion ``h``, knee ``-(h + a)`` and ankle ``a`` sum to zero along
    each leg, so the feet stay parallel to the pelvis and, with an upright
    pelvis, flat. The base is then translated so each foot is planted where
    it starts in the neutral pose, its ankle origin ``sole_depth_m()`` above
    Z=0 -- exactly the ground target ``solve_pose(ground_feet=True)`` uses.
    """
    hip, ankle = 1.0, 0.3  # rad; hip [-0.52, 2.09], ankle [-0.87, 0.35]
    q = pin.neutral(model)
    for side in ("l", "r"):
        _set_joint(model, q, f"hip_{side}_flex", hip)
        _set_joint(model, q, f"knee_{side}_flex", -(hip + ankle))  # [-2.62, 0]
        _set_joint(model, q, f"ankle_{side}_flex", ankle)
    assert np.all(q[7:] >= model.lowerPositionLimit[7:])
    assert np.all(q[7:] <= model.upperPositionLimit[7:])
    planted = _frame_pose(model, pin.neutral(model), FEET[0]).translation.copy()
    planted[2] = sole_depth_m()
    q[:3] += planted - _frame_pose(model, q, FEET[0]).translation
    return q


def _position_residual(
    model: pin.Model, q: np.ndarray, frame: str, target: np.ndarray
) -> float:
    return float(
        np.linalg.norm(_frame_pose(model, q, frame).translation - target[:3, 3])
    )


def _solve_without_warning(
    ik: ModuleType,
    problem: IKProblem,
    targets: dict[str, np.ndarray],
    **kwargs: object,
) -> np.ndarray:
    with warnings.catch_warnings():
        warnings.simplefilter("error", UserWarning)
        q: np.ndarray = ik.solve_pose(problem, targets, **kwargs)
    assert q.shape == (problem.model.nq,)
    assert np.all(np.isfinite(q))
    return q


def test_hand_frame_target_is_reached(ik: ModuleType, problem: IKProblem) -> None:
    model = problem.model
    q_ref = pin.neutral(model)
    _set_joint(model, q_ref, "shoulder_l_flex", 0.8)
    _set_joint(model, q_ref, "elbow_l_flex", 1.0)
    target = _frame_pose(model, q_ref, HAND_FRAME).homogeneous

    q = _solve_without_warning(ik, problem, {HAND_FRAME: target})

    assert _position_residual(model, q, HAND_FRAME, target) < RESIDUAL_BAR_M


def test_ground_target_puts_both_soles_on_the_ground(
    ik: ModuleType, problem: IKProblem
) -> None:
    model = problem.model
    neutral = pin.neutral(model)

    q = _solve_without_warning(ik, problem, {}, ground_feet=True)

    for foot in FEET:
        pose = _frame_pose(model, q, foot)
        assert abs(pose.translation[2] - sole_depth_m()) < RESIDUAL_BAR_M
        # Feet stay planted where they started rather than collapsing to the origin.
        start = _frame_pose(model, neutral, foot).translation
        assert np.linalg.norm(pose.translation[:2] - start[:2]) < RESIDUAL_BAR_M


def test_bar_target_with_grounded_feet_reaches_squat_depth(
    ik: ModuleType, problem: IKProblem
) -> None:
    model = problem.model
    q_ref = _grounded_squat_configuration(model)
    target = _frame_pose(model, q_ref, BAR_FRAME).homogeneous
    standing_bar_z = _frame_pose(model, pin.neutral(model), BAR_FRAME).translation[2]
    standing_bar_z += (
        sole_depth_m() - _frame_pose(model, pin.neutral(model), FEET[0]).translation[2]
    )
    assert target[2, 3] < standing_bar_z - 0.05, "target must be a real squat depth"

    q = _solve_without_warning(ik, problem, {BAR_FRAME: target}, ground_feet=True)

    assert _position_residual(model, q, BAR_FRAME, target) < RESIDUAL_BAR_M
    for foot in FEET:
        assert (
            abs(_frame_pose(model, q, foot).translation[2] - sole_depth_m())
            < RESIDUAL_BAR_M
        )


def test_unknown_target_frame_is_rejected(ik: ModuleType, problem: IKProblem) -> None:
    with pytest.raises(GeometryError, match="no_such_frame"):
        ik.solve_pose(problem, {"no_such_frame": np.eye(4)})
