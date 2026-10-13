"""Public forward kinematics for Pinocchio exercise models."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import ArrayLike

from pinocchio_models.dynamics import _resolve_model
from pinocchio_models.shared.body.foot_sole import sole_corners
from robotics_contracts.preconditions import require_finite, require_shape


def forward_kinematics(exercise: str | Any, q: ArrayLike) -> dict[str, Any]:
    """Compute forward kinematics for an exercise model.

    Computes the placement of every frame (including segments / links and joints)
    in the world coordinate frame using ``pinocchio.forwardKinematics`` and
    ``pinocchio.updateFramePlacements``.

    Args:
        exercise: Manifest exercise id (e.g. ``"squat"``) or a ready
            ``pinocchio.Model``.
        q: Configuration vector, shape ``(model.nq,)``.

    Returns:
        Mapping from frame/segment name to ``pinocchio.SE3`` pose.

    Raises:
        ValueError: Unknown exercise id, wrong shape or non-finite values.
        TypeError: ``exercise`` is neither a str nor a Model.
    """
    import pinocchio as pin

    model = _resolve_model(exercise)
    q_arr = np.asarray(q, dtype=np.float64)
    require_shape(q_arr, (model.nq,), "q")
    require_finite(q_arr, "q")

    data = model.createData()
    pin.forwardKinematics(model, data, q_arr)
    pin.updateFramePlacements(model, data)

    poses: dict[str, pin.SE3] = {
        frame.name: data.oMf[i].copy() for i, frame in enumerate(model.frames)
    }
    return poses


def grounded_pelvis_height(
    exercise: str | Any,
    q: ArrayLike | None = None,
    *,
    data: Any | None = None,
) -> float:
    """Return the pelvis world Z height that grounds the lowest foot sole on the floor (z = 0).

    Evaluates the forward kinematics of the foot sole contact geometries at configuration *q*
    and calculates the vertical shift needed so the lowest point rests on z = 0 (#450).

    Args:
        exercise: Manifest exercise id (e.g. ``"squat"``) or a ready ``pinocchio.Model``.
        q: Optional configuration vector, shape ``(model.nq,)``. If None, uses ``pin.neutral(model)``.
        data: Optional pre-allocated ``pinocchio.Data``.

    Returns:
        The world z-height for the pelvis root.
    """
    import pinocchio as pin

    model = _resolve_model(exercise)
    if q is None:
        q_arr = pin.neutral(model)
    else:
        q_arr = np.asarray(q, dtype=np.float64)
        require_shape(q_arr, (model.nq,), "q")
        require_finite(q_arr, "q")

    if data is None:
        data = model.createData()

    pin.forwardKinematics(model, data, q_arr)
    pin.updateFramePlacements(model, data)

    pelvis_id = model.getFrameId("pelvis")
    current_pelvis_z = (
        float(data.oMf[pelvis_id].translation[2])
        if pelvis_id < len(model.frames)
        else 0.0
    )

    corners = [np.array(c, dtype=np.float64) for c in sole_corners()]
    foot_frames = ("foot_l", "foot_r")
    heights: list[float] = []

    for name in foot_frames:
        frame_id = model.getFrameId(name)
        if frame_id >= len(model.frames):
            continue
        oMf = data.oMf[frame_id]
        for corner in corners:
            p_world = oMf.act(corner)
            heights.append(float(p_world[2]))

    if not heights:
        return current_pelvis_z

    min_sole_z = min(heights)
    return float(current_pelvis_z - min_sole_z)


def ground_configuration(
    exercise: str | Any,
    q: ArrayLike,
    *,
    data: Any | None = None,
) -> np.ndarray:
    """Return a copy of *q* with the pelvis root z-height adjusted so feet rest on the floor.

    When the model has a free-flyer root (floating base pelvis), this updates ``q[2]``
    so the lowest foot sole contact point lies exactly at z = 0. If the model has no
    free-flyer, returns a copy of *q* unchanged (#450).

    Args:
        exercise: Manifest exercise id or ``pinocchio.Model``.
        q: Configuration vector, shape ``(model.nq,)``.
        data: Optional pre-allocated ``pinocchio.Data``.

    Returns:
        Adjusted configuration vector as a new numpy array.
    """
    model = _resolve_model(exercise)
    q_arr = np.array(q, dtype=np.float64, copy=True)
    require_shape(q_arr, (model.nq,), "q")
    require_finite(q_arr, "q")

    if model.njoints < 2 or model.joints[1].nq != 7:
        return q_arr

    z_grounded = grounded_pelvis_height(model, q_arr, data=data)
    q_arr[2] = z_grounded
    return q_arr


__all__ = [
    "forward_kinematics",
    "ground_configuration",
    "grounded_pelvis_height",
]
