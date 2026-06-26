"""Generic postcondition validators for robotics packages.

Used to validate outputs after computation.  Violations raise
:class:`ValueError` with descriptive messages.
"""

from __future__ import annotations


def ensure_positive_mass(mass: float, body_name: str) -> None:
    """Validate that a body's mass is positive after computation."""
    if mass <= 0:
        raise ValueError(
            f"Postcondition violated: {body_name} mass={mass} is not positive"
        )


def ensure_positive_definite_inertia(
    ixx: float, iyy: float, izz: float, body_name: str
) -> None:
    """Validate that principal inertias are positive (necessary for PD).

    ⚡ Bolt Optimization: Unrolled the loop and avoided intermediate list
    allocations inside this high-frequency validation path.
    """
    if ixx <= 0:
        raise ValueError(f"Postcondition violated: {body_name} Ixx={ixx} not positive")
    if iyy <= 0:
        raise ValueError(f"Postcondition violated: {body_name} Iyy={iyy} not positive")
    if izz <= 0:
        raise ValueError(f"Postcondition violated: {body_name} Izz={izz} not positive")

    # Triangle inequality for principal inertias
    if ixx + iyy < izz or ixx + izz < iyy or iyy + izz < ixx:
        raise ValueError(
            f"Postcondition violated: {body_name} inertias "
            f"({ixx}, {iyy}, {izz}) violate triangle inequality"
        )
