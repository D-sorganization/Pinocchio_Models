"""Forward dynamics (``pinocchio.aba``) with compliant ground contact (#430).

Formulation
-----------
Each step evaluates the foot contact points of
:func:`~pinocchio_models.shared.contact.contact_model.foot_contact_points`
(four sole corners per foot), turns their penetration and velocity into
ground forces with the unilateral, friction-limited penalty law of
:mod:`pinocchio_models.shared.contact.penalty`, maps those forces onto the
supporting joints as external spatial forces and solves
``pinocchio.aba(model, data, q, v, tau, fext)`` for the accelerations. The
state is advanced with semi-implicit (symplectic) Euler on the configuration
manifold (``pinocchio.integrate``), with the contact and servo damping taken
linearly implicit: ``v+ = v + dt (M + dt C)^-1 M ddq`` (``M`` from
``pinocchio.crba``). The light foot segments make that damping far too stiff
for an explicit step; implicitly it is unconditionally stable and leaves the
equilibria unchanged.

The contact gains derive from the model weight and a static sole penetration
(:func:`~pinocchio_models.shared.contact.penalty.penalty_contact_params`); the
time step derives from the linearised, undamped stability limit
(:func:`~pinocchio_models.shared.contact.penalty.max_stable_time_step`)
evaluated at the initial state with every contact point closed, divided by
:data:`TIME_STEP_SAFETY_FACTOR`.

The floating root is unactuated: joint torques come from an optional
:class:`JointServo` (PD about a reference posture plus a feed-forward term).
:func:`holding_servo` builds one whose feed-forward torques hold a standing
posture against the static ground reaction of
:func:`~pinocchio_models.contact_dynamics.ground_reaction_forces`.

Limits (why the capability is ``partial``): the floor is a flat compliant
plane at ``z = 0`` touched only by the foot sole corners (no other
body-environment or self collision), friction is viscous-clipped Coulomb
(no static stick), and the step is fixed (no event detection at touchdown).
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike

from pinocchio_models.contact_dynamics import (
    _FREE_FLYER_NV,
    _require_free_flyer_root,
    ground_reaction_forces,
)
from pinocchio_models.dynamics import _resolve_model
from pinocchio_models.shared.contact.contact_model import (
    ContactPoint,
    foot_contact_points,
)
from pinocchio_models.shared.contact.grf import (
    ContactForceSample,
    GroundReactionForces,
    aggregate_ground_reaction,
)
from pinocchio_models.shared.contact.penalty import (
    PenaltyContactParams,
    max_stable_time_step,
    penalty_contact_force,
    penalty_contact_params,
)
from robotics_contracts.preconditions import (
    require_finite,
    require_non_negative,
    require_positive,
    require_shape,
)

#: The step is the linearised stability limit divided by this factor. The
#: limit is evaluated at the initial state; a factor 2 keeps the step stable
#: while effective contact masses shrink up to 4x (``omega ~ 1/sqrt(m)``)
#: as the configuration evolves.
TIME_STEP_SAFETY_FACTOR: float = 2.0

#: Default servo bandwidth (rad/s): a factor 3.5 below the 70 rad/s
#: supported-body contact mode of the default penalty gains, so the servo
#: and contact modes stay separated.
DEFAULT_SERVO_BANDWIDTH_RAD_S: float = 20.0

#: Default servo damping ratio (critical).
DEFAULT_SERVO_DAMPING_RATIO: float = 1.0

#: Relative root-wrench residual tolerated in the static holding torques. The
#: rigid contact solve balances the weight to round-off (measured < 1e-15 W on
#: every free-root exercise), while an unsupported posture (e.g. no foot on the
#: floor) leaves a residual of order W; 1e-6 W separates the two with margin.
_HOLDING_RESIDUAL_REL_TOL: float = 1e-6


@dataclass(frozen=True)
class JointServo:
    """Joint-space PD servo with feed-forward torque; the root is unactuated.

    ``tau = tau_ff + kp * difference(q, q_ref) - kd * v`` with the six root
    entries forced to zero.

    Attributes:
        q_ref: Reference configuration, shape ``(nq,)``.
        kp: Per-velocity-coordinate stiffness, shape ``(nv,)`` (N m/rad).
        kd: Per-velocity-coordinate damping, shape ``(nv,)`` (N m s/rad).
        tau_ff: Feed-forward torque, shape ``(nv,)`` (N m).
    """

    q_ref: np.ndarray
    kp: np.ndarray
    kd: np.ndarray
    tau_ff: np.ndarray

    def __post_init__(self) -> None:
        """Validate shapes, finiteness and non-negative gains."""
        if np.ndim(self.kp) != 1:
            raise ValueError(f"kp must be one-dimensional, got {np.shape(self.kp)}")
        nv = len(self.kp)
        for value, name in ((self.kd, "kd"), (self.tau_ff, "tau_ff")):
            require_shape(np.asarray(value), (nv,), name)
        for value, name in (
            (self.q_ref, "q_ref"),
            (self.kp, "kp"),
            (self.kd, "kd"),
            (self.tau_ff, "tau_ff"),
        ):
            require_finite(np.asarray(value), name)
        if np.any(np.asarray(self.kp) < 0.0) or np.any(np.asarray(self.kd) < 0.0):
            raise ValueError("servo gains kp and kd must be non-negative")


@dataclass(frozen=True)
class ForwardDynamicsStep:
    """Accelerations and ground reaction at one state.

    Attributes:
        ddq: Generalised accelerations from ``pinocchio.aba``, ``(nv,)``.
        grf: Ground reaction of the penalty contacts at this state.
    """

    ddq: np.ndarray
    grf: GroundReactionForces


@dataclass(frozen=True)
class ForwardDynamicsRollout:
    """State trajectory of a contact forward-dynamics rollout.

    Attributes:
        time: Sample times, shape ``(n + 1,)`` (s).
        q: Configurations, shape ``(n + 1, nq)``.
        v: Velocities, shape ``(n + 1, nv)``.
        ground_force: Total ground force on the body at each sample,
            shape ``(n + 1, 3)`` (N); zero without ground contact.
        min_contact_height: Lowest contact-point height at each sample,
            shape ``(n + 1,)`` (m); negative values are penetration.
        dt: Integration step (s).
        contact_params: Penalty gains used, or ``None`` without contact.
        final_grf: Ground reaction at the last sample.
    """

    time: np.ndarray
    q: np.ndarray
    v: np.ndarray
    ground_force: np.ndarray
    min_contact_height: np.ndarray
    dt: float
    contact_params: PenaltyContactParams | None
    final_grf: GroundReactionForces


def default_contact_params(
    exercise: str | Any, *, contacts: Sequence[ContactPoint] | None = None
) -> PenaltyContactParams:
    """Penalty gains derived from the model weight and its contact points.

    Args:
        exercise: Manifest exercise id or a ready ``pinocchio.Model``.
        contacts: Contact points sharing the weight; defaults to
            :func:`foot_contact_points`.

    Returns:
        :class:`PenaltyContactParams` from :func:`penalty_contact_params`.
    """
    model = _resolve_model(exercise)
    points = _contact_points(contacts)
    g = _gravity(model)
    return penalty_contact_params(_total_mass(model) * g, len(points), gravity=g)


def holding_servo(
    exercise: str | Any,
    q: ArrayLike,
    *,
    bandwidth_rad_s: float = DEFAULT_SERVO_BANDWIDTH_RAD_S,
    damping_ratio: float = DEFAULT_SERVO_DAMPING_RATIO,
) -> JointServo:
    """Servo that holds the standing posture *q* on the ground.

    Gains per joint coordinate ``i`` follow from its articulated inertia
    ``M_ii`` (``pinocchio.crba``): ``kp = M_ii w^2`` and
    ``kd = 2 zeta M_ii w``, so every joint has the bandwidth ``w``. The
    feed-forward torque is the static joint torque that, together with the
    rigid ground reaction of :func:`ground_reaction_forces`, balances
    gravity: ``tau_ff = g(q) - J^T w_ground``.

    Args:
        exercise: Manifest exercise id or a ready ``pinocchio.Model``.
        q: Standing configuration, shape ``(nq,)``.
        bandwidth_rad_s: Servo bandwidth ``w`` (rad/s).
        damping_ratio: Servo damping ratio ``zeta``.

    Returns:
        The :class:`JointServo`.

    Raises:
        ValueError: Invalid inputs (see :func:`ground_reaction_forces`), or
            the ground reaction does not balance the root wrench.
    """
    import pinocchio as pin

    model = _resolve_model(exercise)
    q_arr = _config(model, q)
    require_positive(bandwidth_rad_s, "bandwidth_rad_s")
    require_non_negative(damping_ratio, "damping_ratio")
    data = model.createData()
    inertia = np.diag(pin.crba(model, data, q_arr)).copy()
    inertia[:_FREE_FLYER_NV] = 0.0
    tau_ff = _static_holding_torque(pin, model, data, q_arr)
    return JointServo(
        q_ref=q_arr,
        kp=inertia * bandwidth_rad_s**2,
        kd=2.0 * damping_ratio * inertia * bandwidth_rad_s,
        tau_ff=tau_ff,
    )


def contact_forward_dynamics(
    exercise: str | Any,
    q: ArrayLike,
    v: ArrayLike,
    tau: ArrayLike,
    *,
    contact_params: PenaltyContactParams | None = None,
    contacts: Sequence[ContactPoint] | None = None,
) -> ForwardDynamicsStep:
    """Accelerations ``aba(q, v, tau, fext)`` with penalty ground contact.

    Args:
        exercise: Manifest exercise id or a ready ``pinocchio.Model`` with a
            free-flyer root.
        q: Configuration, shape ``(nq,)``.
        v: Velocity, shape ``(nv,)``.
        tau: Generalised forces, shape ``(nv,)``; the six root entries must
            be zero (the floating base is unactuated).
        contact_params: Penalty gains; defaults to
            :func:`default_contact_params`.
        contacts: Contact points; defaults to :func:`foot_contact_points`.

    Returns:
        :class:`ForwardDynamicsStep` with accelerations and ground reaction.

    Raises:
        ValueError: Wrong shapes, non-finite values, actuated root, welded
            root, unknown contact frame.
    """
    model = _resolve_model(exercise)
    params = contact_params or default_contact_params(model, contacts=contacts)
    sim = _ContactSimulator(model, _contact_points(contacts), params)
    q_arr, v_arr = _config(model, q), _velocity(model, v)
    tau_arr = _velocity(model, tau, "tau")
    _require_unactuated_root(tau_arr)
    ddq, samples = sim.accelerations(q_arr, v_arr, tau_arr)
    return ForwardDynamicsStep(ddq=ddq, grf=sim.ground_reaction(samples))


def simulate_forward_dynamics(
    exercise: str | Any,
    q0: ArrayLike,
    v0: ArrayLike | None = None,
    *,
    duration: float,
    dt: float | None = None,
    servo: JointServo | None = None,
    ground_contact: bool = True,
    contact_params: PenaltyContactParams | None = None,
    contacts: Sequence[ContactPoint] | None = None,
) -> ForwardDynamicsRollout:
    """Integrate ``pinocchio.aba`` with penalty ground contact over *duration*.

    Args:
        exercise: Manifest exercise id or a ready ``pinocchio.Model`` with a
            free-flyer root.
        q0: Initial configuration, shape ``(nq,)``.
        v0: Initial velocity, shape ``(nv,)``; zero when omitted.
        duration: Simulated time (s).
        dt: Integration step (s). Defaults to the linearised stability
            limit divided by :data:`TIME_STEP_SAFETY_FACTOR` (capped at
            *duration*); an explicit step above that bound is rejected.
        servo: Joint torques; the joints are passive when omitted.
        ground_contact: ``False`` disables the floor (free fall).
        contact_params: Penalty gains; defaults to
            :func:`default_contact_params`.
        contacts: Contact points; defaults to :func:`foot_contact_points`.

    Returns:
        The :class:`ForwardDynamicsRollout` (``ceil(duration / dt)`` steps).

    Raises:
        ValueError: Invalid inputs, an unstable explicit ``dt``, or a
            non-finite state during integration.
    """
    import pinocchio as pin

    model = _resolve_model(exercise)
    q_arr = _config(model, q0)
    v_arr = np.zeros(model.nv) if v0 is None else _velocity(model, v0, "v0")
    require_positive(duration, "duration")
    points = _contact_points(contacts)
    params = None
    if ground_contact:
        params = contact_params or default_contact_params(model, contacts=points)
    sim = _ContactSimulator(model, points, params)
    if servo is not None:
        _require_servo_matches(model, servo)
    step = _resolve_time_step(sim, q_arr, servo, duration, dt)

    n_steps = int(np.ceil(duration / step - 1e-9))
    qs, vs = np.empty((n_steps + 1, model.nq)), np.empty((n_steps + 1, model.nv))
    forces, heights = np.empty((n_steps + 1, 3)), np.empty(n_steps + 1)
    for k in range(n_steps + 1):
        tau = _servo_torque(pin, model, servo, q_arr, v_arr)
        ddq, samples = sim.accelerations(q_arr, v_arr, tau)
        qs[k], vs[k] = q_arr, v_arr
        forces[k] = sum((s.force for s in samples), np.zeros(3))
        heights[k] = sim.min_height
        if k == n_steps:
            final = sim.ground_reaction(samples)
            break
        v_arr = v_arr + sim.velocity_increment(q_arr, ddq, servo, step)
        q_arr = np.asarray(pin.integrate(model, q_arr, step * v_arr))
        require_finite(np.concatenate([q_arr, v_arr]), "integrated state")

    return ForwardDynamicsRollout(
        time=step * np.arange(n_steps + 1),
        q=qs,
        v=vs,
        ground_force=forces,
        min_contact_height=heights,
        dt=step,
        contact_params=params,
        final_grf=final,
    )


class _ContactSimulator:
    """Penalty contact forces and ``aba`` for one model (internal)."""

    def __init__(
        self,
        model: Any,
        points: Sequence[ContactPoint],
        params: PenaltyContactParams | None,
    ) -> None:
        import pinocchio as pin

        _require_free_flyer_root(model)
        for cp in points:
            if not model.existFrame(cp.frame_name):
                raise ValueError(f"contact frame {cp.frame_name!r} not in model")
            if tuple(cp.normal) != (0.0, 0.0, 1.0):
                raise ValueError("penalty contact requires the Z-up floor normal")
        self._pin = pin
        self._model = model
        self._data = model.createData()
        self._points = list(points)
        self._feet = list(dict.fromkeys(cp.frame_name for cp in points))
        self._frames = [model.getFrameId(cp.frame_name) for cp in points]
        self._params = params
        self._in_contact = [False] * len(self._points)
        self.min_height = float("inf")

    def accelerations(
        self, q: np.ndarray, v: np.ndarray, tau: np.ndarray
    ) -> tuple[np.ndarray, list[ContactForceSample]]:
        """Return ``aba`` accelerations and the active contact samples."""
        pin, model, data = self._pin, self._model, self._data
        pin.forwardKinematics(model, data, q, v)
        pin.updateFramePlacements(model, data)
        fext = pin.StdVec_Force()
        for _ in range(model.njoints):
            fext.append(pin.Force.Zero())
        samples = []
        self.min_height = float("inf")
        self._in_contact = [False] * len(self._points)
        for index, (cp, frame_id) in enumerate(
            zip(self._points, self._frames, strict=True)
        ):
            position, velocity = self._point_state(cp, frame_id)
            self.min_height = min(self.min_height, float(position[2]))
            if self._params is None or position[2] > 0.0:
                continue
            self._in_contact[index] = True
            force = penalty_contact_force(position, velocity, cp.mu, self._params)
            joint = model.frames[frame_id].parentJoint
            world = pin.Force(force, np.cross(position, force))
            fext[joint] = fext[joint] + data.oMi[joint].actInv(world)
            samples.append(
                ContactForceSample(foot=cp.frame_name, position=position, force=force)
            )
        ddq = np.array(pin.aba(model, data, q, v, tau, fext))
        require_finite(ddq, "ddq")
        return ddq, samples

    def ground_reaction(
        self, samples: Sequence[ContactForceSample]
    ) -> GroundReactionForces:
        """Aggregate active samples into per-foot and total GRF."""
        return aggregate_ground_reaction(samples, self._feet)

    def velocity_increment(
        self,
        q: np.ndarray,
        ddq: np.ndarray,
        servo: JointServo | None,
        dt: float,
    ) -> np.ndarray:
        """``dt (M + dt C)^-1 M ddq``: the step with linearly implicit damping.

        ``C`` holds the damping of the contact points in contact at *q*
        (those below the floor in the last :meth:`accelerations` call) and of
        the servo. Must follow :meth:`accelerations` at the same *q*.
        """
        mass, _stiffness, damping = self.linearised_matrices(
            q, servo, closed=self._in_contact
        )
        return dt * np.linalg.solve(mass + dt * damping, mass @ ddq)

    def linearised_matrices(
        self,
        q: np.ndarray,
        servo: JointServo | None,
        closed: Sequence[bool] | None = None,
    ) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
        """``(M, K, C)`` at *q*; contact points in *closed* (default all)."""
        pin, model, data = self._pin, self._model, self._data
        mass = np.array(pin.crba(model, data, q))
        mass = np.triu(mass) + np.triu(mass, 1).T
        pin.computeJointJacobians(model, data, q)
        pin.updateFramePlacements(model, data)
        stiffness = np.zeros_like(mass)
        damping = np.zeros_like(mass)
        flags = [True] * len(self._points) if closed is None else list(closed)
        if self._params is not None:
            for cp, frame_id, flag in zip(
                self._points, self._frames, flags, strict=True
            ):
                if not flag:
                    continue
                jac = self._point_jacobian(cp, frame_id)
                normal, tangent = jac[2:3], jac[:2]
                stiffness += self._params.stiffness * normal.T @ normal
                damping += self._params.damping * normal.T @ normal
                damping += self._params.tangential_damping * tangent.T @ tangent
        if servo is not None:
            stiffness += np.diag(servo.kp)
            damping += np.diag(servo.kd)
        return mass, stiffness, damping

    def _point_state(
        self, cp: ContactPoint, frame_id: int
    ) -> tuple[np.ndarray, np.ndarray]:
        """World position and velocity of a contact point."""
        pin = self._pin
        placement = self._data.oMf[frame_id]
        position = np.asarray(placement.act(np.asarray(cp.local_position)))
        twist = pin.getFrameVelocity(
            self._model, self._data, frame_id, pin.ReferenceFrame.LOCAL_WORLD_ALIGNED
        )
        lever = position - np.asarray(placement.translation)
        velocity = np.asarray(twist.linear) + np.cross(twist.angular, lever)
        return position, velocity

    def _point_jacobian(self, cp: ContactPoint, frame_id: int) -> np.ndarray:
        """``(3, nv)`` world-axes Jacobian of a contact point."""
        pin = self._pin
        jac = np.asarray(
            pin.getFrameJacobian(
                self._model,
                self._data,
                frame_id,
                pin.ReferenceFrame.LOCAL_WORLD_ALIGNED,
            )
        )
        placement = self._data.oMf[frame_id]
        lever = placement.act(np.asarray(cp.local_position)) - placement.translation
        return jac[:3] - _skew(np.asarray(lever)) @ jac[3:]


def _resolve_time_step(
    sim: _ContactSimulator,
    q: np.ndarray,
    servo: JointServo | None,
    duration: float,
    dt: float | None,
) -> float:
    """Default or validate the step against the linearised stability limit.

    The limit is taken for the *undamped* system ``(M, K, 0)``. Implicit
    damping only enlarges the stable region (``h omega <= 2 (zeta +
    sqrt(1 + zeta^2))``), but a step that leans on heavy damping for
    stability under-samples the contact modes: the undamped limit is
    ``2 / omega_max``, so with the safety factor 2 the stiffest contact or
    servo mode is sampled at ``h omega_max <= 1`` (>= 2 pi steps per period).
    """
    mass, stiffness, _damping = sim.linearised_matrices(q, servo)
    limit = max_stable_time_step(
        mass, stiffness, np.zeros_like(mass), upper_bound=duration
    )
    bound = limit / TIME_STEP_SAFETY_FACTOR if limit < duration else duration
    if dt is None:
        return bound
    require_positive(dt, "dt")
    if dt > bound:
        raise ValueError(
            f"dt={dt:g} s exceeds the stable step {bound:g} s "
            f"(linearised limit {limit:g} s / safety {TIME_STEP_SAFETY_FACTOR:g})"
        )
    return dt


def _static_holding_torque(
    pin: Any, model: Any, data: Any, q: np.ndarray
) -> np.ndarray:
    """``g(q) - J^T w`` for the rigid static ground reaction ``w``."""
    zeros = np.zeros(model.nv)
    torque = np.array(pin.rnea(model, data, q, zeros, zeros))
    grf = ground_reaction_forces(model, q)
    pin.computeJointJacobians(model, data, q)
    pin.updateFramePlacements(model, data)
    for name, foot in grf.per_foot.items():
        frame_id = model.getFrameId(name)
        origin = np.asarray(data.oMf[frame_id].translation)
        wrench = np.concatenate(
            [foot.force, foot.moment - np.cross(origin, foot.force)]
        )
        jac = pin.getFrameJacobian(
            model, data, frame_id, pin.ReferenceFrame.LOCAL_WORLD_ALIGNED
        )
        torque -= np.asarray(jac).T @ wrench
    weight = _total_mass(model) * _gravity(model)
    residual = float(np.abs(torque[:_FREE_FLYER_NV]).max())
    if residual > _HOLDING_RESIDUAL_REL_TOL * weight:
        raise ValueError(
            f"ground reaction does not balance the root wrench (residual "
            f"{residual:g} N); the posture is not statically supported"
        )
    torque[:_FREE_FLYER_NV] = 0.0
    return torque


def _servo_torque(
    pin: Any, model: Any, servo: JointServo | None, q: np.ndarray, v: np.ndarray
) -> np.ndarray:
    """Joint torques of *servo* (zero when absent), root entries zero."""
    if servo is None:
        return np.zeros(model.nv)
    error = np.asarray(pin.difference(model, q, servo.q_ref))
    tau = servo.tau_ff + servo.kp * error - servo.kd * v
    tau[:_FREE_FLYER_NV] = 0.0
    return np.asarray(tau)


def _require_servo_matches(model: Any, servo: JointServo) -> None:
    """Precondition: the servo is sized for *model*."""
    require_shape(np.asarray(servo.q_ref), (model.nq,), "servo.q_ref")
    require_shape(np.asarray(servo.kp), (model.nv,), "servo.kp")


def _require_unactuated_root(tau: np.ndarray) -> None:
    """Precondition: no generalised force on the floating base."""
    if np.any(tau[:_FREE_FLYER_NV] != 0.0):
        raise ValueError("tau must be zero on the six unactuated root coordinates")


def _contact_points(contacts: Sequence[ContactPoint] | None) -> list[ContactPoint]:
    """Return the contact points, defaulting to the foot sole corners."""
    points = list(contacts) if contacts is not None else foot_contact_points()
    if not points:
        raise ValueError("at least one contact point is required")
    return points


def _config(model: Any, q: ArrayLike) -> np.ndarray:
    """Validated configuration array."""
    q_arr = np.array(q, dtype=np.float64)
    require_shape(q_arr, (model.nq,), "q")
    require_finite(q_arr, "q")
    return q_arr


def _velocity(model: Any, v: ArrayLike, name: str = "v") -> np.ndarray:
    """Validated velocity-sized array."""
    v_arr = np.array(v, dtype=np.float64)
    require_shape(v_arr, (model.nv,), name)
    require_finite(v_arr, name)
    return v_arr


def _total_mass(model: Any) -> float:
    """Total mass of the model (kg)."""
    return float(sum(inertia.mass for inertia in model.inertias))


def _gravity(model: Any) -> float:
    """Magnitude of the model gravity (m/s^2)."""
    return float(np.linalg.norm(np.asarray(model.gravity.linear)))


def _skew(r: np.ndarray) -> np.ndarray:
    """Cross-product matrix ``[r]_x`` with ``[r]_x w = r x w``."""
    return np.array([[0.0, -r[2], r[1]], [r[2], 0.0, -r[0]], [-r[1], r[0], 0.0]])


__all__ = [
    "DEFAULT_SERVO_BANDWIDTH_RAD_S",
    "DEFAULT_SERVO_DAMPING_RATIO",
    "TIME_STEP_SAFETY_FACTOR",
    "ForwardDynamicsRollout",
    "ForwardDynamicsStep",
    "JointServo",
    "contact_forward_dynamics",
    "default_contact_params",
    "holding_servo",
    "simulate_forward_dynamics",
]
