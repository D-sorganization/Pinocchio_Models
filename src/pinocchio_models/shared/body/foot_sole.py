"""Sole geometry shared by foot contacts and foot collision (#471).

The biomechanics parity standard places the sole ``foot.length`` below the
ankle origin (``pose_frame``). Contact points and the sole collision box
must use that same depth so they rest on the floor at a lift's start pose.
"""

from __future__ import annotations

from functools import lru_cache

from pinocchio_models.shared.parity._canonical import conformance, topology

SOLE_COLLISION_DIMS: tuple[float, float, float] = (0.26, 0.10, 0.02)


@lru_cache(maxsize=1)
def sole_depth_m() -> float:
    """Return the distance (m) from the ankle origin down to the sole.

    Postcondition: strictly positive.
    """
    depth = float(topology.dimension(conformance.load_standard(), "foot.length"))
    if depth <= 0.0:
        raise ValueError(f"foot.length must be positive, got {depth}")
    return depth


def sole_corners(
    dims: tuple[float, float, float] = SOLE_COLLISION_DIMS,
) -> list[tuple[float, float, float]]:
    """Return the 8 bounding box corners of the sole in the foot link frame.

    The box bottom sits ``sole_depth_m()`` below the ankle origin.
    """
    depth = sole_depth_m()
    length, width, height = dims
    x_half = length / 2.0
    y_half = width / 2.0
    z_min = -depth
    z_max = -depth + height
    return [
        (x, y, z)
        for x in (-x_half, x_half)
        for y in (-y_half, y_half)
        for z in (z_min, z_max)
    ]
