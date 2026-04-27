"""Contact point and specification models for exercise simulations.

Defines contact frames used by Pinocchio's constraint formulations
rather than built-in collision detection.  Each exercise has a
:class:`ContactSpec` describing where the body contacts the environment
(ground via feet, bench surface, barbell grip, etc.).

Foot contact uses four corner points on a rectangular sole (0.26 x 0.10 m),
matching the collision geometry added to the URDF.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

from pinocchio_models.shared.constants import VALID_EXERCISE_NAMES
from pinocchio_models.exceptions import GeometryError

logger = logging.getLogger(__name__)

# Sole rectangle dimensions (meters).
_SOLE_LENGTH: float = 0.26  # X (anterior-posterior)
_SOLE_WIDTH: float = 0.10  # Y (medial-lateral)
_SOLE_THICKNESS: float = 0.02  # Z (vertical)

# Default friction coefficient (rubber-on-rubber / shoe-on-platform).
_DEFAULT_MU: float = 0.8


@dataclass(frozen=True)
class ContactPoint:
    """A contact point on a body frame.

    Attributes
    ----------
    frame_name : str
        Pinocchio frame name (e.g. ``"foot_l"``).
    local_position : tuple[float, float, float]
        Position in the body frame (meters).
    normal : tuple[float, float, float]
        Outward contact normal (default: Z-up).
    mu : float
        Coulomb friction coefficient.
    """

    frame_name: str
    local_position: tuple[float, float, float]
    normal: tuple[float, float, float] = (0.0, 0.0, 1.0)
    mu: float = _DEFAULT_MU


@dataclass(frozen=True)
class ContactSpec:
    """Contact specification for an exercise.

    Attributes
    ----------
    foot_contacts : list[ContactPoint]
        Foot-ground contact points (always present).
    bench_contact : ContactPoint | None
        Back-on-bench contact for bench press.
    barbell_contacts : list[ContactPoint] | None
        Hand-on-barbell contacts for deadlift / olympic lifts.
    """

    foot_contacts: list[ContactPoint] = field(default_factory=list)
    bench_contact: ContactPoint | None = None
    barbell_contacts: list[ContactPoint] | None = None


def _foot_corner_contacts(frame_name: str) -> list[ContactPoint]:
    """Return four corner contact points for a foot sole rectangle.

    Points are at the corners of a 0.26 x 0.10 m rectangle offset
    -0.01 m below the foot frame origin (bottom of sole).
    """
    half_length = _SOLE_LENGTH / 2.0
    half_width = _SOLE_WIDTH / 2.0
    z_offset = -_SOLE_THICKNESS / 2.0  # Bottom of the sole box

    corners = [
        ("heel_med", (-half_length, -half_width, z_offset)),
        ("heel_lat", (-half_length, half_width, z_offset)),
        ("toe_med", (half_length, -half_width, z_offset)),
        ("toe_lat", (half_length, half_width, z_offset)),
    ]
    return [
        ContactPoint(
            frame_name=frame_name,
            local_position=pos,
        )
        for _label, pos in corners
    ]


def _both_feet_contacts() -> list[ContactPoint]:
    """Return foot corner contacts for both left and right feet."""
    return _foot_corner_contacts("foot_l") + _foot_corner_contacts("foot_r")


def _bench_contact_for(exercise_name: str) -> ContactPoint | None:
    """Return the back-on-bench contact point if *exercise_name* needs one."""
    if exercise_name != "bench_press":
        return None
    return ContactPoint(
        frame_name="torso",
        local_position=(0.0, 0.0, -0.05),
        normal=(0.0, 0.0, 1.0),
        mu=0.6,
    )


def _barbell_contacts_for(exercise_name: str) -> list[ContactPoint] | None:
    """Return hand-on-barbell contacts for barbell-grip exercises."""
    if exercise_name not in ("deadlift", "snatch", "clean_and_jerk"):
        return None
    return [
        ContactPoint(
            frame_name="hand_l",
            local_position=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            mu=0.9,
        ),
        ContactPoint(
            frame_name="hand_r",
            local_position=(0.0, 0.0, 0.0),
            normal=(0.0, 0.0, 1.0),
            mu=0.9,
        ),
    ]


def _validate_exercise_name(exercise_name: str) -> None:
    """Validate contact lookup input before building a contact spec."""
    if exercise_name not in VALID_EXERCISE_NAMES:
        raise GeometryError(
            f"Unknown exercise '{exercise_name}'. "
            f"Valid names: {sorted(VALID_EXERCISE_NAMES)}"
        )


def _build_contact_spec(exercise_name: str) -> ContactSpec:
    """Assemble the contact spec for a validated exercise name."""
    return ContactSpec(
        foot_contacts=_both_feet_contacts(),
        bench_contact=_bench_contact_for(exercise_name),
        barbell_contacts=_barbell_contacts_for(exercise_name),
    )


def get_exercise_contacts(exercise_name: str, model: Any = None) -> ContactSpec:
    """Return contact specification for the given exercise.

    Creates 4 contact points per foot (corners of sole rectangle):
    heel-medial, heel-lateral, toe-medial, toe-lateral for each side.

    Parameters
    ----------
    exercise_name : str
        One of the valid exercise names.
    model : Any, optional
        Pinocchio model (reserved for future frame-index validation).

    Returns
    -------
    ContactSpec
        Contact specification with foot contacts and any exercise-
        specific contacts (bench, barbell).

    Raises
    ------
    ValueError
        If *exercise_name* is not recognised.
    """
    _validate_exercise_name(exercise_name)
    return _build_contact_spec(exercise_name)