"""Constrained contact dynamics: ground reaction forces and CoP (#432).

Formulation
-----------
The Pinocchio adapter solves a **quasi-static standing** problem that is
well posed for a rigid, redundant foot contact:

1. Every non-root joint is locked at ``q`` (``pinocchio.buildReducedModel``),
   i.e. the joints are held by ideal servos. The exercise becomes one rigid
   free-flying body carrying the full mass and inertia of the model.
2. The foot contact points of :func:`~pinocchio_models.shared.contact.\
contact_model.foot_contact_points` (four sole corners per foot) whose world
   height is within ``contact_tolerance_m`` of the floor (``z = 0``) become
   rigid bilateral ``CONTACT_3D`` constraints expressed
   ``LOCAL_WORLD_ALIGNED``.
3. ``pinocchio.constraintDynamics`` solves the constrained forward dynamics
   at ``v = 0``, ``tau = 0`` with proximal regularisation. Eight corner
   points over-constrain the six root degrees of freedom; the proximal
   solver returns the minimum-norm force distribution among the redundant
   contacts. With three or more non-collinear active points the body cannot
   accelerate, so the total contact force balances the weight exactly
   (``F_z = m g``).

The per-point forces are then aggregated by the engine-independent
:mod:`pinocchio_models.shared.contact.grf` into per-foot and total wrenches
and a centre of pressure. Contacts are bilateral: a foot may pull on the floor
if the centre of mass lies outside the support polygon; callers check
:func:`~pinocchio_models.shared.contact.grf.point_in_convex_polygon`.
Without any active contact point the result is the explicit no-contact case
(zero force and moment, ``cop=None``).
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

import numpy as np
from numpy.typing import ArrayLike

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
from robotics_contracts.preconditions import (
    require_finite,
    require_non_negative,
    require_shape,
)

#: Height (m) within which a contact point counts as touching the floor.
DEFAULT_CONTACT_TOLERANCE_M: float = 1e-3

#: Proximal settings for ``pinocchio.constraintDynamics``. ``mu > 0`` makes the
#: redundant (rank-deficient) contact system solvable; the absolute accuracy
#: bounds the constraint residual.
_PROX_ACCURACY: float = 1e-12
_PROX_MU: float = 1e-8
_PROX_MAX_ITER: int = 100

_FREE_FLYER_NQ: int = 7
_FREE_FLYER_NV: int = 6


def ground_reaction_forces(
    exercise: str | Any,
    q: ArrayLike,
    *,
    contact_tolerance_m: float = DEFAULT_CONTACT_TOLERANCE_M,
    contacts: Sequence[ContactPoint] | None = None,
) -> GroundReactionForces:
    """Per-foot and total ground reaction forces and CoP at configuration *q*.

    Solves the quasi-static, joint-locked constrained contact dynamics
    described in this module's docstring.

    Args:
        exercise: Manifest exercise id (e.g. ``"squat"``) or a ready
            ``pinocchio.Model``; the model must have a free-flyer root.
        q: Configuration, shape ``(model.nq,)``.
        contact_tolerance_m: A contact point is active when its world height
            is at most this far above the floor (``z = 0``).
        contacts: Contact points to use; defaults to the foot sole corners
            of :func:`foot_contact_points`. Feet are grouped by frame name.

    Returns:
        :class:`GroundReactionForces` with one entry per foot frame.

    Raises:
        ValueError: Unknown exercise id, welded (non free-flyer) root, wrong
            shape or non-finite ``q``, negative tolerance, unknown frame.
        TypeError: ``exercise`` is neither a str nor a Model.
    """
    import pinocchio as pin

    model = _resolve_model(exercise)
    q_arr = np.asarray(q, dtype=np.float64)
    require_shape(q_arr, (model.nq,), "q")
    require_finite(q_arr, "q")
    require_non_negative(contact_tolerance_m, "contact_tolerance_m")
    _require_free_flyer_root(model)
    points = list(contacts) if contacts is not None else foot_contact_points()
    feet = list(dict.fromkeys(cp.frame_name for cp in points))

    rigid = pin.buildReducedModel(model, list(range(2, model.njoints)), q_arr)
    rigid.gravity = model.gravity
    q_root = q_arr[:_FREE_FLYER_NQ].copy()
    data = rigid.createData()
    pin.framesForwardKinematics(rigid, data, q_root)

    active = [
        (cp, anchor)
        for cp in points
        if (anchor := _contact_anchor(pin, rigid, data, cp))[1][2]
        <= contact_tolerance_m
    ]
    if not active:
        return aggregate_ground_reaction([], feet)

    forces = _solve_contact_forces(pin, rigid, data, q_root, active)
    samples = [
        ContactForceSample(foot=cp.frame_name, position=anchor[1], force=force)
        for (cp, anchor), force in zip(active, forces, strict=True)
    ]
    return aggregate_ground_reaction(samples, feet)


def _require_free_flyer_root(model: Any) -> None:
    """Precondition: joint 1 is a free flyer (a welded root has no GRF)."""
    if model.njoints < 2 or model.joints[1].nq != _FREE_FLYER_NQ:
        raise ValueError(
            "ground contact requires a free-flyer root; "
            "welded-root models (e.g. bench_press) have no ground contact"
        )


def _contact_anchor(
    pin: Any, model: Any, data: Any, cp: ContactPoint
) -> tuple[Any, np.ndarray]:
    """Return ``(joint placement of the point, world position of the point)``."""
    if not model.existFrame(cp.frame_name):
        raise ValueError(f"contact frame {cp.frame_name!r} not in model")
    frame_id = model.getFrameId(cp.frame_name)
    local = np.asarray(cp.local_position, dtype=np.float64)
    joint_placement = model.frames[frame_id].placement * pin.SE3(np.eye(3), local)
    world = np.asarray(data.oMf[frame_id].act(local), dtype=np.float64)
    return joint_placement, world


def _solve_contact_forces(
    pin: Any,
    model: Any,
    data: Any,
    q_root: np.ndarray,
    active: Sequence[tuple[ContactPoint, tuple[Any, np.ndarray]]],
) -> np.ndarray:
    """Solve ``constraintDynamics`` and return the ``(n, 3)`` contact forces."""
    contact_models = pin.StdVec_RigidConstraintModel()
    for cp, (placement, _world) in active:
        contact_models.append(
            pin.RigidConstraintModel(
                pin.ContactType.CONTACT_3D,
                model,
                model.frames[model.getFrameId(cp.frame_name)].parentJoint,
                placement,
                pin.ReferenceFrame.LOCAL_WORLD_ALIGNED,
            )
        )
    contact_datas = pin.StdVec_RigidConstraintData()
    for contact_model in contact_models:
        contact_datas.append(contact_model.createData())
    _init_constraint_dynamics(pin, model, data, contact_models, contact_datas)

    prox = pin.ProximalSettings(_PROX_ACCURACY, _PROX_MU, _PROX_MAX_ITER)
    zeros = np.zeros(_FREE_FLYER_NV)
    pin.constraintDynamics(
        model, data, q_root, zeros, zeros, contact_models, contact_datas, prox
    )
    forces = np.asarray(data.lambda_c, dtype=np.float64).reshape(len(active), 3)
    require_finite(forces, "contact forces")
    return forces


def _init_constraint_dynamics(
    pin: Any, model: Any, data: Any, contact_models: Any, contact_datas: Any
) -> None:
    """Call ``initConstraintDynamics`` across its Pinocchio 3 and 4 signatures."""
    try:
        pin.initConstraintDynamics(model, data, contact_models, contact_datas)
    except TypeError:  # Pinocchio 3.x: (model, data, contact_models)
        pin.initConstraintDynamics(model, data, contact_models)


__all__ = ["DEFAULT_CONTACT_TOLERANCE_M", "ground_reaction_forces"]
