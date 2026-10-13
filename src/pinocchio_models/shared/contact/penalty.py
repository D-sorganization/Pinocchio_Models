"""Compliant (penalty) ground contact and explicit-integration stability (#430).

Engine-independent NumPy math for the forward-dynamics rollout in
:mod:`pinocchio_models.forward_dynamics`. The Pinocchio adapter supplies the
contact-point kinematics and integrates ``pinocchio.aba``; everything here is
unit-tested without an engine.

Why a penalty model
-------------------
A rollout needs a contact law that (a) is unilateral -- the floor pushes but
never pulls, so a foot can lift off -- (b) bounds friction by the Coulomb
cone, and (c) is defined for every state, including the first touchdown. A
compliant spring-damper per contact point satisfies all three with a closed
form force, and feeds ``aba`` as an external force. The rigid bilateral
``constraintDynamics`` solve of :mod:`pinocchio_models.contact_dynamics`
cannot release a contact or bound friction, so it is used for the static
holding torques only, not for integration.

Gain derivation
---------------
With ``n`` contact points sharing a body of weight ``W`` and a chosen static
penetration ``delta`` (the floor/sole compliance):

* normal stiffness per point ``k = W / (n * delta)``, so a body resting on all
  points sinks exactly ``delta``;
* the supported-body vertical mode then has ``omega = sqrt(n k / M) =
  sqrt(g / delta)``, independent of the mass;
* normal damping per point ``c = 2 zeta sqrt(k M / n)`` gives that mode the
  damping ratio ``zeta`` (critical by default, so touchdown does not bounce);
* tangential (viscous) friction uses the same coefficient ``c``, clipped to the
  Coulomb cone ``|F_t| <= mu F_n``. Sliding velocities therefore decay with
  the time constant ``1 / (2 zeta omega)`` until the cone saturates.

Integrator and time-step derivation
-----------------------------------
The rollout integrates semi-implicit (symplectic) Euler with **linearly
implicit damping**: ``(M + h C) (v+ - v) = h F(q, v)``, ``q+ = q + h v+``,
where ``C = -dF/dv`` is the contact and servo damping. Damping of the light
foot segments (ankle inertia ~2e-3 kg m^2) is far too stiff for an explicit
step -- it would force ``h`` ~ 1e-5 s -- but treated implicitly it is
unconditionally stable, and the fixed points (``F = 0``) are unchanged.
:func:`max_stable_time_step` returns the largest step for which the
linearised system ``M x'' + C x' + K x = 0`` stays stable under this scheme
(spectral radius of the one-step map <= 1). For a single oscillator the
limit is ``h omega <= 2 (zeta + sqrt(1 + zeta^2))``: damping only helps.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from robotics_contracts.preconditions import (
    require_finite,
    require_non_negative,
    require_positive,
    require_shape,
)

#: Default static sole penetration (m): shoe sole / platform compliance of a
#: few millimetres. Sets the supported-body contact mode to
#: ``sqrt(g / delta)`` = 70 rad/s (11 Hz).
DEFAULT_STATIC_PENETRATION_M: float = 2e-3

#: Default damping ratio of the supported-body contact mode (critical).
DEFAULT_CONTACT_DAMPING_RATIO: float = 1.0

#: Spectral radius above 1 tolerated as round-off. Undamped zero-stiffness
#: directions (free drift) give a defective eigenvalue 1 whose computed
#: value is perturbed by ``O(sqrt(machine eps))`` ~ 1e-8; 1e-6 clears that by
#: two orders of magnitude while a genuinely unstable mode exceeds it at once.
_SPECTRAL_RADIUS_TOL: float = 1e-6

#: Relative width of the bisection bracket at which the search stops.
_BISECTION_REL_TOL: float = 1e-3


@dataclass(frozen=True)
class PenaltyContactParams:
    """Per-point compliant ground contact gains.

    Attributes:
        stiffness: Normal stiffness ``k`` (N/m).
        damping: Normal damping ``c`` (N s/m).
        tangential_damping: Viscous friction coefficient (N s/m), clipped to
            the Coulomb cone at each point.
    """

    stiffness: float
    damping: float
    tangential_damping: float

    def __post_init__(self) -> None:
        """Validate the gains (stiffness positive, dampings non-negative)."""
        require_positive(self.stiffness, "stiffness")
        require_non_negative(self.damping, "damping")
        require_non_negative(self.tangential_damping, "tangential_damping")


def penalty_contact_params(
    weight_n: float,
    n_points: int,
    *,
    static_penetration_m: float = DEFAULT_STATIC_PENETRATION_M,
    damping_ratio: float = DEFAULT_CONTACT_DAMPING_RATIO,
    gravity: float = 9.80665,
) -> PenaltyContactParams:
    """Derive per-point contact gains from the body weight (see module doc).

    Args:
        weight_n: Weight ``W = M g`` carried by the contacts (N).
        n_points: Number of contact points sharing the weight.
        static_penetration_m: Static sink ``delta`` with all points loaded.
        damping_ratio: Damping ratio ``zeta`` of the supported-body mode.
        gravity: Gravitational acceleration ``g`` used to recover ``M``.

    Returns:
        The derived :class:`PenaltyContactParams`.

    Raises:
        ValueError: Non-positive weight, point count, penetration or gravity,
            or a negative damping ratio.
    """
    require_positive(weight_n, "weight_n")
    require_positive(float(n_points), "n_points")
    require_positive(static_penetration_m, "static_penetration_m")
    require_non_negative(damping_ratio, "damping_ratio")
    require_positive(gravity, "gravity")
    stiffness = weight_n / (n_points * static_penetration_m)
    mass_per_point = weight_n / gravity / n_points
    damping = 2.0 * damping_ratio * float(np.sqrt(stiffness * mass_per_point))
    return PenaltyContactParams(
        stiffness=stiffness, damping=damping, tangential_damping=damping
    )


def penalty_contact_force(
    position: ArrayLike,
    velocity: ArrayLike,
    mu: float,
    params: PenaltyContactParams,
    ground_height: float = 0.0,
) -> np.ndarray:
    """Ground force on one contact point (world axes, Z up).

    The point is in contact when it is below ``ground_height``. The normal
    force ``k d - c v_z`` (``d`` the penetration) is clamped at zero so the
    floor never pulls; the viscous tangential force ``-c_t v_xy`` is clipped
    to the Coulomb cone ``mu F_n``.

    Args:
        position: World position of the point, shape ``(3,)``.
        velocity: World velocity of the point, shape ``(3,)``.
        mu: Coulomb friction coefficient (>= 0).
        params: Contact gains.
        ground_height: Height of the floor plane.

    Returns:
        Force ``(F_x, F_y, F_z)`` with ``F_z >= 0`` and
        ``|(F_x, F_y)| <= mu F_z``.

    Raises:
        ValueError: Wrong shape or non-finite input, negative ``mu``.
    """
    p = _vec3(position, "position")
    v = _vec3(velocity, "velocity")
    require_non_negative(mu, "mu")
    penetration = ground_height - p[2]
    if penetration <= 0.0:
        return np.zeros(3)
    normal = max(params.stiffness * penetration - params.damping * v[2], 0.0)
    tangential = -params.tangential_damping * v[:2]
    limit = mu * normal
    magnitude = float(np.hypot(*tangential))
    if magnitude > limit:
        tangential *= limit / magnitude
    return np.array([tangential[0], tangential[1], normal])


def integrator_spectral_radius(
    mass: ArrayLike, stiffness: ArrayLike, damping: ArrayLike, dt: float
) -> float:
    """Spectral radius of one integrator step of ``M x'' + C x' + K x = 0``.

    The step is ``v+ = v + dt (M + dt C)^-1 (-K x - C v)``,
    ``x+ = x + dt v+`` (semi-implicit Euler, linearly implicit damping).

    Args:
        mass: Symmetric positive-definite mass matrix ``(n, n)``.
        stiffness: Stiffness matrix ``(n, n)``.
        damping: Damping matrix ``(n, n)``.
        dt: Time step (s).

    Returns:
        The largest eigenvalue magnitude of the one-step map.

    Raises:
        ValueError: Mismatched or non-square shapes, non-finite entries,
            non-positive ``dt``.
        numpy.linalg.LinAlgError: ``mass`` is not positive definite.
    """
    m, k, c = _square_triplet(mass, stiffness, damping)
    require_positive(dt, "dt")
    np.linalg.cholesky(m)  # raises LinAlgError unless M is positive definite
    effective = np.linalg.inv(m + dt * c)
    a, b = effective @ k, effective @ c
    eye = np.eye(len(m))
    v_row = np.hstack([-dt * a, eye - dt * b])  # v+ as a function of (x, v)
    x_row = np.hstack([eye, np.zeros_like(eye)]) + dt * v_row
    step = np.vstack([x_row, v_row])
    return float(np.max(np.abs(np.linalg.eigvals(step))))


def max_stable_time_step(
    mass: ArrayLike,
    stiffness: ArrayLike,
    damping: ArrayLike,
    *,
    upper_bound: float,
) -> float:
    """Largest step at which semi-implicit Euler stays linearly stable.

    Bisects the stability limit of :func:`integrator_spectral_radius`
    to a relative bracket of 1e-3, returning the stable end of the bracket.

    Args:
        mass: Symmetric positive-definite mass matrix ``(n, n)``.
        stiffness: Stiffness matrix ``(n, n)``.
        damping: Damping matrix ``(n, n)``.
        upper_bound: Largest step of interest; returned when the system is
            stable all the way up to it (e.g. no stiffness at all).

    Returns:
        The stable time step (s), ``<= upper_bound``.

    Raises:
        ValueError: Invalid matrices or non-positive ``upper_bound``.
    """
    require_positive(upper_bound, "upper_bound")

    def stable(dt: float) -> bool:
        radius = integrator_spectral_radius(mass, stiffness, damping, dt)
        return radius <= 1.0 + _SPECTRAL_RADIUS_TOL

    if stable(upper_bound):
        return upper_bound
    low, high = 0.0, upper_bound
    while high - low > _BISECTION_REL_TOL * high:
        mid = 0.5 * (low + high)
        low, high = (mid, high) if stable(mid) else (low, mid)
    if low <= 0.0:
        raise ValueError("no stable time step found above zero")
    return low


def _square_triplet(
    mass: ArrayLike, stiffness: ArrayLike, damping: ArrayLike
) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Validate three equally sized, finite square matrices."""
    m = np.asarray(mass, dtype=np.float64)
    if m.ndim != 2 or m.shape[0] != m.shape[1] or m.shape[0] == 0:
        raise ValueError(f"mass must be a non-empty square matrix, got {m.shape}")
    out = []
    for arr, name in ((m, "mass"), (stiffness, "stiffness"), (damping, "damping")):
        matrix = np.asarray(arr, dtype=np.float64)
        require_shape(matrix, m.shape, name)
        require_finite(matrix, name)
        out.append(matrix)
    return out[0], out[1], out[2]


def _vec3(value: ArrayLike, name: str) -> np.ndarray:
    """Return *value* as a finite float ``(3,)`` array or raise ``ValueError``."""
    arr = np.asarray(value, dtype=np.float64)
    require_shape(arr, (3,), name)
    require_finite(arr, name)
    return arr


__all__ = [
    "DEFAULT_CONTACT_DAMPING_RATIO",
    "DEFAULT_STATIC_PENETRATION_M",
    "PenaltyContactParams",
    "max_stable_time_step",
    "penalty_contact_force",
    "penalty_contact_params",
    "integrator_spectral_radius",
]
