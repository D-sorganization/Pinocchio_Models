"""Public inverse dynamics (RNEA) for Pinocchio exercise models."""

from __future__ import annotations

from typing import Any

import numpy as np
from numpy.typing import ArrayLike

from robotics_contracts.preconditions import require_finite, require_shape


def _resolve_model(exercise: str | Any) -> Any:
    """Return a free-flyer ``pinocchio.Model`` for a manifest id or a Model."""
    if isinstance(exercise, str):
        from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

        return load_model(build_urdf(exercise))
    if hasattr(exercise, "nq") and hasattr(exercise, "nv"):
        return exercise
    raise TypeError(
        "exercise must be a manifest exercise id (str) or a pinocchio.Model, "
        f"got {type(exercise).__name__}"
    )


def inverse_dynamics(
    exercise: str | Any, q: ArrayLike, v: ArrayLike, a: ArrayLike
) -> np.ndarray:
    """Generalized forces ``tau = rnea(model, q, v, a)`` for an exercise model.

    The model is free-flyer rooted with standard gravity, so in a static pose
    (``v = a = 0``) the root vertical force ``tau[2]`` equals ``m * g``.

    Args:
        exercise: Manifest exercise id (e.g. ``"squat"``) or a ready
            ``pinocchio.Model``.
        q: Configuration, shape ``(model.nq,)``.
        v: Velocity, shape ``(model.nv,)``.
        a: Acceleration, shape ``(model.nv,)``.

    Returns:
        ``tau`` with shape ``(model.nv,)``.

    Raises:
        ValueError: Unknown exercise id, wrong shapes or non-finite values.
        TypeError: ``exercise`` is neither a str nor a Model.
    """
    import pinocchio as pin

    model = _resolve_model(exercise)
    q_arr = np.asarray(q, dtype=np.float64)
    v_arr = np.asarray(v, dtype=np.float64)
    a_arr = np.asarray(a, dtype=np.float64)
    for arr, shape, name in (
        (q_arr, (model.nq,), "q"),
        (v_arr, (model.nv,), "v"),
        (a_arr, (model.nv,), "a"),
    ):
        require_shape(arr, shape, name)
        require_finite(arr, name)

    tau = np.array(pin.rnea(model, model.createData(), q_arr, v_arr, a_arr))
    require_finite(tau, "tau")
    return tau


__all__ = ["inverse_dynamics"]
