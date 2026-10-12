"""Joint axes and joint origins of the full-body model, from the parity standard.

The vendored parity standard (``_canonical/biomech_parity_standard.json``) is
the single source of truth for the kinematic topology: the canonical frame is
Z-up, X forward, Y left, every joint frame is aligned with the world at q=0
(no rotated joint origins), so the ``<axis>`` literal of a coordinate equals
its canonical axis. Left bilateral segments sit at +Y, right at -Y.
"""

from __future__ import annotations

from functools import lru_cache

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
