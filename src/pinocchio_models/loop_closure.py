"""Right-hand bar loop closure for the spec-start barbell lifts (#501).

``SpecLiftBuilder.attach_barbell`` welds the bar to ``hand_l`` and hangs a
zero-mass marker frame ``barbell_grip_r`` on the shaft at the spec grip
width. A URDF is a tree, so ``hand_r`` is never connected to the bar: without
a constraint the right arm is free in forward dynamics and the bar hangs from
the left hand alone.

This module closes that loop in the engine, as Drake_Models does with its
bar-grip weld: a 6-D rigid constraint (``pinocchio.ContactType.CONTACT_6D``)
between the ``hand_r`` frame and the ``barbell_grip_r`` frame. The reference
relative pose is the one the two frames have at the given start
configuration, so the constraint is satisfied there by construction and holds
the (possibly non-coincident) grip offset of the spec start pose.

The constrained forward dynamics ``pinocchio.constraintDynamics`` returns the
accelerations and the 6-D constraint wrench ``lambda_c``; a mild Baumgarte
corrector bounds the drift of the semi-implicit integration.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import numpy as np
from numpy.typing import ArrayLike

from pinocchio_models.contact_dynamics import (
    _PROX_ACCURACY,
    _PROX_MAX_ITER,
    _PROX_MU,
    _init_constraint_dynamics,
)
from pinocchio_models.dynamics import _resolve_model
from robotics_contracts.preconditions import require_finite, require_shape

#: Frame on the right hand that is welded to the bar by the constraint.
RIGHT_HAND_FRAME: str = "hand_r"

#: Zero-mass marker frame on the shaft at the right grip.
RIGHT_GRIP_FRAME: str = "barbell_grip_r"

#: Baumgarte stiffness (1/s^2) of the constraint corrector; the damping is the
#: critical ``2 sqrt(kp)``. A time constant of ~20 ms stays well inside the
#: stability limit of the contact-dynamics step (~ms) and bounds the
#: integration drift without fighting the constraint solve.
BAUMGARTE_KP: float = 2500.0


@dataclass(frozen=True)
class LoopClosureStep:
    """Constrained accelerations and the loop-closure constraint wrench.

    Attributes:
        ddq: Generalised accelerations of the constrained dynamics, ``(nv,)``.
        wrench: 6-D constraint force/moment (``lambda_c``) the bar exerts to
            hold the right hand, in the constraint frame (N, N m).
    """

    ddq: np.ndarray
    wrench: np.ndarray


def has_right_hand_loop(model: Any) -> bool:
    """Whether *model* has both frames of the right-hand loop closure."""
    return bool(
        model.existFrame(RIGHT_HAND_FRAME) and model.existFrame(RIGHT_GRIP_FRAME)
    )


def right_hand_loop_constraint(
    exercise: str | Any,
    q_ref: ArrayLike,
    *,
    hand_frame: str = RIGHT_HAND_FRAME,
    grip_frame: str = RIGHT_GRIP_FRAME,
) -> Any:
    """6-D ``RigidConstraintModel`` welding *hand_frame* to *grip_frame*.

    The two frames keep the relative pose they have at *q_ref* (normally the
    spec start configuration).

    Args:
        exercise: Manifest exercise id or a ready ``pinocchio.Model``.
        q_ref: Reference configuration, shape ``(model.nq,)``.
        hand_frame: Frame name on the hand; defaults to ``hand_r``.
        grip_frame: Frame name on the bar; defaults to ``barbell_grip_r``.

    Returns:
        A ``pinocchio.RigidConstraintModel`` of type ``CONTACT_6D``.

    Raises:
        ValueError: A frame is not in the model, both frames sit on the same
            joint (nothing to constrain), or *q_ref* is mis-shaped or
            non-finite.
    """
    import pinocchio as pin

    model = _resolve_model(exercise)
    q_arr = _config(model, q_ref)
    for name in (hand_frame, grip_frame):
        if not model.existFrame(name):
            raise ValueError(f"loop-closure frame {name!r} not in model")
    hand_id, grip_id = model.getFrameId(hand_frame), model.getFrameId(grip_frame)
    hand_joint = model.frames[hand_id].parentJoint
    grip_joint = model.frames[grip_id].parentJoint
    if hand_joint == grip_joint:
        raise ValueError(
            f"frames {hand_frame!r} and {grip_frame!r} share joint "
            f"{hand_joint}; there is no loop to close"
        )

    data = model.createData()
    pin.forwardKinematics(model, data, q_arr)
    pin.updateFramePlacements(model, data)
    # The hand frame, expressed in the bar-side joint, is the second contact
    # frame: both contact frames coincide at q_ref, so the error is zero there.
    grip_placement = data.oMi[grip_joint].actInv(data.oMf[hand_id])
    constraint = pin.RigidConstraintModel(
        pin.ContactType.CONTACT_6D,
        model,
        hand_joint,
        model.frames[hand_id].placement,
        grip_joint,
        grip_placement,
        pin.ReferenceFrame.LOCAL,
    )
    _set_baumgarte(pin, constraint)
    return constraint


def _set_baumgarte(pin: Any, constraint: Any) -> None:
    """Set the Baumgarte gains across Pinocchio 3 and 4.

    Pinocchio 3 exposes a mutable ``constraint.corrector``; Pinocchio 4 takes a
    ``BaumgarteCorrectorParameters`` through ``setBaumgarteCorrectorParameters``.
    """
    kd = 2.0 * np.sqrt(BAUMGARTE_KP)
    if hasattr(constraint, "corrector"):
        constraint.corrector.Kp[:] = BAUMGARTE_KP
        constraint.corrector.Kd[:] = kd
        return
    constraint.setBaumgarteCorrectorParameters(
        pin.BaumgarteCorrectorParameters(BAUMGARTE_KP, kd)
    )


def loop_closure_error(
    exercise: str | Any, q: ArrayLike, constraint: Any
) -> np.ndarray:
    """6-D pose error of the loop at *q*: ``log6(c1^-1 c2)``, zero when closed.

    Returns:
        ``(6,)`` array: linear part (m) then angular part (rad).
    """
    import pinocchio as pin

    model = _resolve_model(exercise)
    q_arr = _config(model, q)
    data = model.createData()
    pin.forwardKinematics(model, data, q_arr)
    first = data.oMi[constraint.joint1_id] * constraint.joint1_placement
    second = data.oMi[constraint.joint2_id] * constraint.joint2_placement
    return np.asarray(pin.log6(first.actInv(second)).vector, dtype=np.float64)


def loop_closure_forward_dynamics(
    exercise: str | Any,
    q: ArrayLike,
    v: ArrayLike,
    tau: ArrayLike,
    *,
    q_ref: ArrayLike | None = None,
    constraints: Any = None,
) -> LoopClosureStep:
    """Constrained forward dynamics with the right hand welded to the bar.

    Gravity comes from ``model.gravity``. No ground contact is applied; use
    ``contact_forward_dynamics`` / ``simulate_forward_dynamics`` for the
    combined contact + loop-closure solve.

    Args:
        exercise: Manifest exercise id or a ready ``pinocchio.Model``.
        q: Configuration, shape ``(nq,)``.
        v: Velocity, shape ``(nv,)``.
        tau: Generalised forces, shape ``(nv,)``.
        q_ref: Configuration at which the hand-to-bar offset is taken;
            defaults to *q*. Ignored when *constraints* is given.
        constraints: Ready ``StdVec_RigidConstraintModel`` to use instead of
            the right-hand loop.

    Raises:
        ValueError: Wrong shapes, non-finite values, or missing loop frames.
    """
    model = _resolve_model(exercise)
    q_arr, v_arr = _config(model, q), _vec(model.nv, v, "v")
    tau_arr = _vec(model.nv, tau, "tau")
    if constraints is None:
        reference = q_arr if q_ref is None else q_ref
        constraints = loop_constraint_vector(
            [right_hand_loop_constraint(model, reference)]
        )
    return solve_constrained(model, q_arr, v_arr, tau_arr, constraints)


def loop_constraint_vector(constraints: list[Any]) -> Any:
    """Pack constraint models into the ``StdVec`` Pinocchio expects."""
    import pinocchio as pin

    packed = pin.StdVec_RigidConstraintModel()
    for constraint in constraints:
        packed.append(constraint)
    return packed


def solve_constrained(
    model: Any,
    q: np.ndarray,
    v: np.ndarray,
    tau: np.ndarray,
    constraints: Any,
    data: Any = None,
) -> LoopClosureStep:
    """Run ``pinocchio.constraintDynamics`` for validated state and torques.

    *data* is an optional ready ``model.createData()`` to reuse across steps.
    """
    import pinocchio as pin

    data = model.createData() if data is None else data
    datas = pin.StdVec_RigidConstraintData()
    for constraint in constraints:
        datas.append(constraint.createData())
    _init_constraint_dynamics(pin, model, data, constraints, datas)
    prox = pin.ProximalSettings(_PROX_ACCURACY, _PROX_MU, _PROX_MAX_ITER)
    ddq = np.array(
        pin.constraintDynamics(model, data, q, v, tau, constraints, datas, prox)
    )
    wrench = np.array(data.lambda_c, dtype=np.float64)
    require_finite(ddq, "ddq")
    require_finite(wrench, "loop-closure wrench")
    return LoopClosureStep(ddq=ddq, wrench=wrench)


def _config(model: Any, q: ArrayLike) -> np.ndarray:
    return _vec(model.nq, q, "q")


def _vec(size: int, value: ArrayLike, name: str) -> np.ndarray:
    arr = np.asarray(value, dtype=np.float64)
    require_shape(arr, (size,), name)
    require_finite(arr, name)
    return arr


__all__ = [
    "BAUMGARTE_KP",
    "RIGHT_GRIP_FRAME",
    "RIGHT_HAND_FRAME",
    "LoopClosureStep",
    "has_right_hand_loop",
    "loop_closure_error",
    "loop_closure_forward_dynamics",
    "right_hand_loop_constraint",
]
