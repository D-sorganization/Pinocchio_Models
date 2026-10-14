"""Real-Pinocchio right-hand bar loop closure (issue #501).

``SpecLiftBuilder.attach_barbell`` welds the bar to ``hand_l`` only; the right
grip is a zero-mass marker on the shaft. Without a constraint the right arm is
free in forward dynamics. The loop closure is a 6-D ``CONTACT_6D`` constraint
between ``hand_r`` and ``barbell_grip_r``.

Scenario: the lifter stands on the floor with every joint servo-held except
the right arm, which is released (zero gains and feed-forward). Unconstrained,
the arm collapses under gravity and the hand leaves the bar; closed, the hand
stays on the bar and the constraint carries load.

Tolerances are derived, not tuned: the Baumgarte corrector holds the loop to
millimetres, while the released arm falls by decimetres in the same time, so
``HOLD_TOL_M`` sits well below the free drift and well above the integration
drift.
"""

from __future__ import annotations

import numpy as np
import pinocchio as pin
import pytest

from pinocchio_models import (
    contact_forward_dynamics,
    ground_configuration,
    holding_servo,
    loop_closure_forward_dynamics,
    right_hand_loop_constraint,
    simulate_forward_dynamics,
)
from pinocchio_models.forward_dynamics import JointServo
from pinocchio_models.loop_closure import (
    RIGHT_GRIP_FRAME,
    RIGHT_HAND_FRAME,
    has_right_hand_loop,
    loop_closure_error,
)
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model
from pinocchio_models.shared.utils.urdf_helpers import get_initial_configuration

EXERCISES = ("deadlift", "snatch")
DURATION_S = 0.3
HOLD_TOL_M = 1e-3  # closed loop: position error bound over the horizon
HOLD_TOL_RAD = 5e-3  # closed loop: orientation error bound
FREE_DRIFT_MIN_M = 5e-2  # released arm: must leave the bar by at least this
CLOSED_AT_START_TOL = 1e-9  # exact in exact arithmetic (round-off)


def _setup(exercise: str) -> tuple[pin.Model, np.ndarray]:
    urdf = build_urdf(exercise)
    model = load_model(urdf)
    return model, ground_configuration(model, get_initial_configuration(model, urdf))


def _right_arm_velocity_indices(model: pin.Model) -> list[int]:
    """Velocity indices of the right shoulder, elbow and wrist joints."""
    return [
        model.joints[jid].idx_v
        for jid in range(1, model.njoints)
        if "_r_" in model.names[jid]
        and model.names[jid].split("_")[0] in {"shoulder", "elbow", "wrist"}
    ]


def _released_right_arm_servo(model: pin.Model, q0: np.ndarray) -> JointServo:
    """Holding servo with the right arm's gains and feed-forward removed."""
    servo = holding_servo(model, q0)
    kp, kd, tau_ff = servo.kp.copy(), servo.kd.copy(), servo.tau_ff.copy()
    released = _right_arm_velocity_indices(model)
    kp[released], kd[released], tau_ff[released] = 0.0, 0.0, 0.0
    return JointServo(q_ref=servo.q_ref, kp=kp, kd=kd, tau_ff=tau_ff)


def _max_loop_error(
    model: pin.Model, constraint: object, qs: np.ndarray
) -> tuple[float, float]:
    errors = np.array([loop_closure_error(model, q, constraint) for q in qs])
    return (
        float(np.linalg.norm(errors[:, :3], axis=1).max()),
        float(np.linalg.norm(errors[:, 3:], axis=1).max()),
    )


@pytest.mark.parametrize("exercise", EXERCISES)
def test_constraint_is_6d_and_closed_at_the_start_pose(exercise: str) -> None:
    model, q0 = _setup(exercise)
    assert has_right_hand_loop(model)

    constraint = right_hand_loop_constraint(model, q0)

    assert constraint.type == pin.ContactType.CONTACT_6D
    assert np.abs(loop_closure_error(model, q0, constraint)).max() < (
        CLOSED_AT_START_TOL
    )
    hand_joint = model.frames[model.getFrameId(RIGHT_HAND_FRAME)].parentJoint
    grip_joint = model.frames[model.getFrameId(RIGHT_GRIP_FRAME)].parentJoint
    assert constraint.joint1_id == hand_joint
    assert constraint.joint2_id == grip_joint


@pytest.mark.parametrize("exercise", EXERCISES)
def test_released_right_arm_leaves_the_bar_without_the_loop(exercise: str) -> None:
    model, q0 = _setup(exercise)
    constraint = right_hand_loop_constraint(model, q0)

    rollout = simulate_forward_dynamics(
        model,
        q0,
        duration=DURATION_S,
        servo=_released_right_arm_servo(model, q0),
        loop_closure=False,
    )

    drift, _ = _max_loop_error(model, constraint, rollout.q)
    assert drift > FREE_DRIFT_MIN_M
    assert rollout.loop_wrench is None


@pytest.mark.parametrize("exercise", EXERCISES)
def test_right_hand_stays_on_the_bar_with_the_loop(exercise: str) -> None:
    model, q0 = _setup(exercise)
    constraint = right_hand_loop_constraint(model, q0)

    rollout = simulate_forward_dynamics(
        model,
        q0,
        duration=DURATION_S,
        servo=_released_right_arm_servo(model, q0),
    )

    position, orientation = _max_loop_error(model, constraint, rollout.q)
    assert position < HOLD_TOL_M
    assert orientation < HOLD_TOL_RAD


@pytest.mark.parametrize("exercise", EXERCISES)
def test_loop_wrench_is_reported_and_carries_load(exercise: str) -> None:
    model, q0 = _setup(exercise)
    servo = _released_right_arm_servo(model, q0)
    v0 = np.zeros(model.nv)

    step = contact_forward_dynamics(model, q0, v0, servo.tau_ff)

    assert step.loop_wrench is not None
    assert step.loop_wrench.shape == (6,)
    assert np.all(np.isfinite(step.loop_wrench))
    # The released arm weighs several kilograms; the loop must carry a
    # non-trivial share (>1 N) but cannot exceed the whole system weight.
    weight = sum(i.mass for i in model.inertias) * -model.gravity.linear[2]
    force = float(np.linalg.norm(step.loop_wrench[:3]))
    assert 1.0 < force < weight


@pytest.mark.parametrize("exercise", EXERCISES)
def test_loop_opt_out_reports_no_wrench(exercise: str) -> None:
    model, q0 = _setup(exercise)
    step = contact_forward_dynamics(
        model, q0, np.zeros(model.nv), np.zeros(model.nv), loop_closure=False
    )
    assert step.loop_wrench is None


def test_standalone_constrained_dynamics_reports_wrench() -> None:
    model, q0 = _setup("deadlift")
    zeros = np.zeros(model.nv)
    tau = np.array(pin.rnea(model, model.createData(), q0, zeros, zeros))
    # Tree gravity compensation except the right arm: the loop must act.
    tau[_right_arm_velocity_indices(model)] = 0.0

    step = loop_closure_forward_dynamics(model, q0, np.zeros(model.nv), tau)

    assert step.ddq.shape == (model.nv,)
    assert step.wrench.shape == (6,)
    assert np.linalg.norm(step.wrench[:3]) > 1.0


class TestPreconditions:
    def test_unknown_hand_frame(self) -> None:
        model, q0 = _setup("deadlift")
        with pytest.raises(ValueError, match="nope"):
            right_hand_loop_constraint(model, q0, hand_frame="nope")

    def test_unknown_grip_frame(self) -> None:
        model, q0 = _setup("deadlift")
        with pytest.raises(ValueError, match="nope"):
            right_hand_loop_constraint(model, q0, grip_frame="nope")

    def test_frames_on_same_joint(self) -> None:
        model, q0 = _setup("deadlift")
        with pytest.raises(ValueError, match="no loop to close"):
            right_hand_loop_constraint(
                model, q0, hand_frame=RIGHT_HAND_FRAME, grip_frame=RIGHT_HAND_FRAME
            )

    def test_wrong_shape_q(self) -> None:
        model, q0 = _setup("deadlift")
        with pytest.raises(ValueError):
            right_hand_loop_constraint(model, q0[:-1])

    def test_squat_has_no_right_hand_loop(self) -> None:
        model, q0 = _setup("squat")
        assert not has_right_hand_loop(model)
        step = contact_forward_dynamics(
            model, q0, np.zeros(model.nv), np.zeros(model.nv)
        )
        assert step.loop_wrench is None
