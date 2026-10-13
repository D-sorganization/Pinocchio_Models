"""Real-Pinocchio forward dynamics (``aba``) with ground contact (issue #430).

Pinocchio is a ``dev`` dependency, so this runs in default CI (as
``test_inverse_dynamics.py`` and ``test_contact_grf.py`` do).

Tolerances are derived, not tuned:

* ``W / k`` -- the sink of a body whose whole weight rests on a single
  contact point -- bounds the penetration of any statically supported
  posture, whatever the load split between the points.
* A free-falling body integrated with semi-implicit Euler drops exactly
  ``g T (T + h) / 2`` after ``T / h`` steps, so free fall is checked to
  round-off.
* Newton's law for the whole body, ``m a_com = F_ground + m g``, holds to
  round-off for every single ``aba`` evaluation.
"""

from __future__ import annotations

import numpy as np
import pinocchio as pin
import pytest

from pinocchio_models import (
    contact_forward_dynamics,
    ground_configuration,
    holding_servo,
    simulate_forward_dynamics,
)
from pinocchio_models.forward_dynamics import (
    TIME_STEP_SAFETY_FACTOR,
    JointServo,
    default_contact_params,
)
from pinocchio_models.shared.contact import foot_contact_points
from pinocchio_models.shared.contact.grf import point_in_convex_polygon
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

STANDING = ("gait", "squat")
DURATION_S = 0.5  # > 5 periods of the 70 rad/s contact mode and 3 servo time
# constants (1 / 20 rad/s): long enough to settle onto the floor.

#: Round-off scale for quantities that are exact in exact arithmetic.
ROUND_OFF_REL = 1e-9


def _model(exercise: str) -> pin.Model:
    return load_model(build_urdf(exercise))


def _standing_q(model: pin.Model) -> np.ndarray:
    return ground_configuration(model, pin.neutral(model))


def _weight(model: pin.Model) -> float:
    return sum(i.mass for i in model.inertias) * -model.gravity.linear[2]


def _single_point_sink(model: pin.Model) -> float:
    """``W / k``: sink with the whole weight on one contact point."""
    return _weight(model) / default_contact_params(model).stiffness


@pytest.mark.parametrize("exercise", STANDING)
def test_aba_rollout_with_ground_contact_keeps_standing_model_up(
    exercise: str,
) -> None:
    model = _model(exercise)
    q0 = _standing_q(model)
    bound = _single_point_sink(model)

    rollout = simulate_forward_dynamics(
        model, q0, duration=DURATION_S, servo=holding_servo(model, q0)
    )

    # Never falls through the floor: penetration and root sink stay within
    # the single-point static sink W / k (a few millimetres).
    assert -rollout.min_contact_height.min() <= bound
    assert q0[2] - rollout.q[:, 2].min() <= bound
    # Settled on the floor: the ground carries the weight (1 %: the
    # residual servo transient after 0.5 s is ~0.1 %), with the centre
    # of pressure inside the support polygon.
    grf = rollout.final_grf
    assert grf.total_force[2] == pytest.approx(_weight(model), rel=0.01)
    assert grf.cop is not None
    assert point_in_convex_polygon(grf.cop, grf.support_polygon)
    assert all(foot.in_contact for foot in grf.per_foot.values())


@pytest.mark.parametrize("exercise", STANDING)
def test_without_ground_contact_the_same_model_free_falls(exercise: str) -> None:
    model = _model(exercise)
    q0 = _standing_q(model)
    data = model.createData()

    rollout = simulate_forward_dynamics(
        model, q0, duration=DURATION_S, ground_contact=False, dt=1e-3
    )

    t_end, h = rollout.time[-1], rollout.dt
    drop = (
        pin.centerOfMass(model, data, q0)[2]
        - (pin.centerOfMass(model, data, rollout.q[-1])[2])
    )
    g = -model.gravity.linear[2]
    assert drop == pytest.approx(0.5 * g * t_end * (t_end + h), rel=ROUND_OFF_REL)
    np.testing.assert_array_equal(rollout.ground_force, 0.0)


def test_passive_model_collapses_but_feet_stay_on_floor() -> None:
    model = _model("squat")
    q0 = _standing_q(model)

    rollout = simulate_forward_dynamics(model, q0, duration=DURATION_S)

    assert q0[2] - rollout.q[-1, 2] > 0.1  # unactuated joints buckle
    assert -rollout.min_contact_height.min() <= _single_point_sink(model)


def test_single_step_obeys_newton_for_the_whole_body() -> None:
    model = _model("gait")
    q = _standing_q(model)
    q[2] -= 0.5 * _single_point_sink(model) / len(foot_contact_points())
    v = np.zeros(model.nv)
    params = default_contact_params(model)
    data = model.createData()
    pin.framesForwardKinematics(model, data, q)
    penetration = sum(
        max(
            0.0,
            -data.oMf[model.getFrameId(cp.frame_name)].act(
                np.asarray(cp.local_position)
            )[2],
        )
        for cp in foot_contact_points()
    )

    step = contact_forward_dynamics(model, q, v, np.zeros(model.nv))

    # At rest the penalty law is the spring alone: F_z = k * total penetration.
    assert penetration > 0.0
    assert step.grf.total_force[2] == pytest.approx(
        params.stiffness * penetration, rel=ROUND_OFF_REL
    )
    pin.centerOfMass(model, data, q, v, step.ddq)
    mass = sum(i.mass for i in model.inertias)
    np.testing.assert_allclose(
        mass * np.asarray(data.acom[0]),
        step.grf.total_force + mass * np.asarray(model.gravity.linear),
        atol=ROUND_OFF_REL * _weight(model),
    )


def test_single_step_above_floor_is_free_fall() -> None:
    model = _model("gait")
    q = _standing_q(model)
    q[2] += 0.01

    step = contact_forward_dynamics("gait", q, np.zeros(model.nv), np.zeros(model.nv))

    assert not step.grf.in_contact
    np.testing.assert_allclose(
        step.ddq[:3], model.gravity.linear, atol=ROUND_OFF_REL * 10
    )


def test_holding_servo_balances_the_static_ground_reaction() -> None:
    model = _model("squat")
    q0 = _standing_q(model)

    servo = holding_servo(model, q0)

    np.testing.assert_array_equal(servo.tau_ff[:6], 0.0)
    np.testing.assert_array_equal(servo.kp[:6], 0.0)
    assert np.all(servo.kp[6:] > 0.0)
    assert np.any(servo.tau_ff[6:] != 0.0)


def test_default_step_is_half_the_stability_limit_and_explicit_step_checked() -> None:
    model = _model("gait")
    q0 = _standing_q(model)
    servo = holding_servo(model, q0)
    rollout = simulate_forward_dynamics(model, q0, duration=0.01, servo=servo)
    unstable = rollout.dt * TIME_STEP_SAFETY_FACTOR * 1.01

    with pytest.raises(ValueError, match="exceeds the stable step"):
        simulate_forward_dynamics(model, q0, duration=0.01, dt=unstable, servo=servo)


class TestPreconditions:
    def setup_method(self) -> None:
        self.model = _model("gait")
        self.q = _standing_q(self.model)
        self.zeros = np.zeros(self.model.nv)

    def test_actuated_root_rejected(self) -> None:
        tau = self.zeros.copy()
        tau[2] = 1.0
        with pytest.raises(ValueError, match="unactuated root"):
            contact_forward_dynamics(self.model, self.q, self.zeros, tau)

    def test_welded_root_rejected(self) -> None:
        bench = _model("bench_press")
        zeros = np.zeros(bench.nv)
        with pytest.raises(ValueError, match="free-flyer"):
            contact_forward_dynamics(bench, pin.neutral(bench), zeros, zeros)

    def test_wrong_shapes(self) -> None:
        with pytest.raises(ValueError, match="q must have shape"):
            contact_forward_dynamics(self.model, np.zeros(3), self.zeros, self.zeros)
        with pytest.raises(ValueError, match="v0 must have shape"):
            simulate_forward_dynamics(self.model, self.q, np.zeros(3), duration=0.1)

    def test_non_finite_state(self) -> None:
        v = self.zeros.copy()
        v[0] = np.nan
        with pytest.raises(ValueError, match="non-finite"):
            contact_forward_dynamics(self.model, self.q, v, self.zeros)

    def test_non_positive_duration(self) -> None:
        with pytest.raises(ValueError, match="duration"):
            simulate_forward_dynamics(self.model, self.q, duration=0.0)

    def test_unknown_contact_frame(self) -> None:
        bad = [foot_contact_points()[0].__class__("nope", (0.0, 0.0, 0.0))]
        with pytest.raises(ValueError, match="not in model"):
            contact_forward_dynamics(
                self.model, self.q, self.zeros, self.zeros, contacts=bad
            )

    def test_holding_servo_rejects_unsupported_posture(self) -> None:
        lifted = self.q.copy()
        lifted[2] += 0.1  # no foot within the contact tolerance of the floor
        with pytest.raises(ValueError, match="not statically supported"):
            holding_servo(self.model, lifted)

    def test_servo_size_mismatch(self) -> None:
        servo = JointServo(
            q_ref=np.zeros(3), kp=np.zeros(2), kd=np.zeros(2), tau_ff=np.zeros(2)
        )
        with pytest.raises(ValueError, match="servo.q_ref"):
            simulate_forward_dynamics(self.model, self.q, duration=0.1, servo=servo)

    def test_negative_servo_gain(self) -> None:
        with pytest.raises(ValueError, match="non-negative"):
            JointServo(
                q_ref=np.zeros(3),
                kp=-np.ones(2),
                kd=np.zeros(2),
                tau_ff=np.zeros(2),
            )
