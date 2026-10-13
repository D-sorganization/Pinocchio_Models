"""Sole geometry shared by foot contacts and foot collision (#471).

The biomechanics parity standard places the sole ``foot.length`` below the
ankle origin (``pose_frame``). Contact points and the sole collision box
must use that same depth so they rest on the floor at a lift's start pose.
"""

from __future__ import annotations

from functools import lru_cache

from pinocchio_models.shared.parity._canonical import conformance, topology


@lru_cache(maxsize=1)
def sole_depth_m() -> float:
    """Return the distance (m) from the ankle origin down to the sole.

    Postcondition: strictly positive.
    """
    depth = float(topology.dimension(conformance.load_standard(), "foot.length"))
    if depth <= 0.0:
        raise ValueError(f"foot.length must be positive, got {depth}")
    return depth
