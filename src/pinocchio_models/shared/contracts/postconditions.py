"""Design-by-Contract postcondition checks.

Used to validate outputs after computation -- catches bugs in model
generation before they propagate to downstream URDF or simulation.

All violations raise ValueError (not AssertionError) so they cannot
be disabled with ``python -O``.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET


def ensure_valid_urdf(xml_string: str) -> ET.Element:
    """Parse *xml_string* and return the root element.

    Validates that the string is well-formed XML with a <robot> root tag.
    Raises ValueError if the string is not valid URDF.
    """
    try:
        root = ET.fromstring(xml_string)  # nosec B314 — parsing self-generated XML
    except ET.ParseError as exc:
        raise ValueError(f"Generated URDF is not well-formed XML: {exc}") from exc
    if root.tag != "robot":
        raise ValueError(f"URDF root must be <robot>, got <{root.tag}>")
    return root


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
