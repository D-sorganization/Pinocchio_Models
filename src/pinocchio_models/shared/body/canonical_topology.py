"""Joint axes and joint origins of the full-body model, from the parity standard.

The vendored parity standard (``_canonical/biomech_parity_standard.json``) is
the single source of truth for the kinematic topology: the canonical frame is
Z-up, X forward, Y left, every joint frame is aligned with the world at q=0
(no rotated joint origins), so the ``<axis>`` literal of a coordinate equals
its canonical axis. Left bilateral segments sit at +Y, right at -Y.
"""

from __future__ import annotations

import math
from functools import lru_cache

from pinocchio_models.exceptions import GeometryError
from pinocchio_models.shared.parity._canonical import conformance, kinematics, topology

Vec3 = tuple[float, float, float]

# Lateral sign per side: left is canonical +Y, right is -Y.
SIDE_SIGN: dict[str, float] = {"l": 1.0, "r": -1.0}

_STD = conformance.load_standard()


@lru_cache(maxsize=1)
def _axes() -> dict[str, Vec3]:
    return kinematics.expected_axes(_STD)


@lru_cache(maxsize=1)
def _offsets() -> dict[str, Vec3]:
    """Segment origin relative to its parent at the standard's own height."""
    return {seg: off for seg, _parent, off in topology.joints(_STD)}


def joint_axis(coordinate: str) -> Vec3:
    """Canonical axis of a standard coordinate, e.g. ``hip_l_adduct``.

    Raises:
        KeyError: If *coordinate* is not a standard coordinate name.
    """
    return _axes()[coordinate]


def joint_offset(segment: str, height: float) -> Vec3:
    """Origin of *segment* in its parent for a body of *height* metres.

    *segment* is a canonical segment name (``torso``, ``thigh_l``, ...). The
    standard's offsets are fixed fractions of height, so they scale linearly.

    Raises:
        KeyError: If *segment* has no joint in the standard.
    """
    scale = height / float(_STD["anthropometrics"]["height_m"])
    x, y, z = _offsets()[segment]
    return (x * scale, y * scale, z * scale)


def solve_grip_abduction(grip_half_width: float, height: float) -> float:
    """Shoulder-adduction angle (rad) that places the hand at *grip_half_width*.

    With the elbow extended, flexion of the lumbar spine or the shoulder is a
    rotation about the shared Y axis and therefore never moves the hand's
    lateral (Y) position (issue #443): only the shoulder's adduction
    coordinate does. Because the standard's convention is "positive toward
    the midline" (mirrored per side), a *negative* result abducts both arms
    outward symmetrically when applied to ``shoulder_l_adduct`` and
    ``shoulder_r_adduct`` with the same raw value.

    Precondition: ``grip_half_width > 0`` and reachable with the elbow
    extended, i.e. ``|shoulder_lateral_offset - grip_half_width| <= arm_length``.

    Raises:
        ValueError: If *grip_half_width* is not positive.
        GeometryError: If the grip is not reachable with the elbow extended.
    """
    if grip_half_width <= 0.0:
        raise ValueError(f"grip_half_width must be positive, got {grip_half_width}")
    shoulder_y = joint_offset("upper_arm_l", height)[1]
    arm_length = (
        -joint_offset("forearm_l", height)[2] - joint_offset("hand_l", height)[2]
    )
    sin_theta = (shoulder_y - grip_half_width) / arm_length
    if abs(sin_theta) > 1.0:
        raise GeometryError(
            f"grip_half_width={grip_half_width:.4f} m is unreachable with the "
            f"elbow extended (shoulder offset {shoulder_y:.4f} m, arm length "
            f"{arm_length:.4f} m)"
        )
    return math.asin(sin_theta)
