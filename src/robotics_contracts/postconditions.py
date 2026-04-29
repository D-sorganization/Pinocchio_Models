"""Generic postcondition validators for robotics packages.

Used to validate outputs after computation.  Violations raise
:class:`ValueError` with descriptive messages.
"""

from __future__ import annotations

import math


def ensure_positive_mass(mass: float, body_name: str) -> None:
    """Validate that a body's mass is positive after computation."""
    if mass <= 0:
        raise ValueError(
            f"Postcondition violated: {body_name} mass={mass} is not positive"
        )


def ensure_positive_definite_inertia(
    ixx: float, iyy: float, izz: float, body_name: str
) -> None:
    """Validate that principal inertias are positive (necessary for PD)."""
    for label, val in [("Ixx", ixx), ("Iyy", iyy), ("Izz", izz)]:
        if val <= 0:
            raise ValueError(
                f"Postcondition violated: {body_name} {label}={val} not positive"
            )
    # Triangle inequality for principal inertias
    if ixx + iyy < izz or ixx + izz < iyy or iyy + izz < ixx:
        raise ValueError(
            f"Postcondition violated: {body_name} inertias "
            f"({ixx}, {iyy}, {izz}) violate triangle inequality"
        )
