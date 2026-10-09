"""Public forward kinematics for Pinocchio exercise models."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import ArrayLike

from pinocchio_models.dynamics import _resolve_model
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


__all__ = ["forward_kinematics"]
