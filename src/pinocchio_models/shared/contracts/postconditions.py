"""Design-by-Contract postcondition checks.

Used to validate outputs after computation -- catches bugs in model
generation before they propagate to downstream URDF or simulation.

All violations raise GeometryError (not AssertionError) so they cannot
be disabled with ``python -O``.
"""

from __future__ import annotations

import logging
import re
import xml.etree.ElementTree as ET
from pinocchio_models.exceptions import URDFError

logger = logging.getLogger(__name__)


def _parse_robot_root(xml_string: str) -> ET.Element:
    """Parse *xml_string* and verify the root element is ``<robot>``."""
    try:
        root = ET.fromstring(xml_string)  # nosec B314 — parsing self-generated XML
    except ET.ParseError as exc:
        raise URDFError(f"Generated URDF is not well-formed XML: {exc}") from exc
    if root.tag != "robot":
        raise URDFError(f"URDF root must be <robot>, got <{root.tag}>")
    return root


def _collect_link_names(root: ET.Element) -> set[str]:
    """Return the set of declared ``<link name=...>`` values under *root*."""
    return {el.get("name", "") for el in root.findall("link") if el.get("name")}


def _validate_joint_links(root: ET.Element, link_names: set[str]) -> None:
    """Validate joint parent/child references and the single-parent rule."""
    child_parent_map: dict[str, str] = {}
    for joint in root.findall("joint"):
        joint_name = joint.get("name", "<unnamed>")

        parent_el = joint.find("parent")
        child_el = joint.find("child")
        if parent_el is None or child_el is None:
            continue

        parent_link = parent_el.get("link", "")
        child_link = child_el.get("link", "")

        # (a) Warn if parent link name does not exist in the declared link set.
        # This may be intentional for aliased parent links in the body model.
        if parent_link and parent_link not in link_names:
            logger.warning(
                "Joint '%s' references parent link '%s' which is not in the "
                "declared link set — verify this is intentional",
                joint_name,
                parent_link,
            )

        # (b) Verify child link name exists in the declared link set.
        if child_link and child_link not in link_names:
            raise URDFError(
                f"Joint '{joint_name}' references unknown child link '{child_link}'"
            )

        # (c) Assert no link appears as child of more than one joint
        # (URDF single-parent-per-link constraint).
        if child_link in child_parent_map:
            raise URDFError(
                f"Link '{child_link}' is declared as child of both "
                f"'{child_parent_map[child_link]}' and '{joint_name}' — "
                "URDF requires each link to have exactly one parent joint"
            )
        if child_link:
            child_parent_map[child_link] = joint_name


_VALID_TAG_PATTERN = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_\-\.]*$")
_VALID_TAG_MATCH = _VALID_TAG_PATTERN.match


def ensure_valid_urdf_tree(root: ET.Element) -> ET.Element:
    """Validate a URDF ElementTree and return the root element.

    Validates:
    1. Root tag is ``<robot>``.
    2. Every joint's ``child`` link name exists in the declared link set.
    3. No link appears as ``child`` of more than one joint (single-parent rule).
    4. All tags must be valid XML identifiers.

    Parent link names are checked with a warning only, because the body model
    uses resolved parent aliases (e.g. ``torso_l`` → ``torso``) that are
    structurally intentional and do not need to match a declared link name.

    Raises ValueError if any check fails.
    """
    if root.tag != "robot":
        raise URDFError(f"URDF root must be <robot>, got <{root.tag}>")

    # Validate all tags are valid XML to replicate the parsing check
    for el in root.iter():
        tag = el.tag
        if type(tag) is str:
            if not _VALID_TAG_MATCH(tag):
                raise URDFError(
                    f"Generated URDF is not well-formed XML: invalid tag '{tag}'"
                )
        else:
            # ElementTree stores comments and processing instructions as
            # callables in the .tag field, so we skip them.
            continue
    link_names = _collect_link_names(root)
    _validate_joint_links(root, link_names)
    return root


def ensure_valid_urdf(xml_string: str) -> ET.Element:
    """Parse *xml_string* and return the root element.

    Validates:
    1. Well-formed XML with a ``<robot>`` root tag.
    2. Every joint's ``child`` link name exists in the declared link set.
    3. No link appears as ``child`` of more than one joint (single-parent rule).

    Parent link names are checked with a warning only, because the body model
    uses resolved parent aliases (e.g. ``torso_l`` → ``torso``) that are
    structurally intentional and do not need to match a declared link name.

    Raises ValueError if any check fails.
    """
    root = _parse_robot_root(xml_string)
    return ensure_valid_urdf_tree(root)


def ensure_positive_mass(mass: float, body_name: str) -> None:
    """Validate that a body's mass is positive after computation."""
    if mass <= 0:
        raise URDFError(
            f"Postcondition violated: {body_name} mass={mass} is not positive"
        )


def ensure_positive_definite_inertia(
    ixx: float, iyy: float, izz: float, body_name: str
) -> None:
    """Validate that principal inertias are positive (necessary for PD)."""
    for label, val in [("Ixx", ixx), ("Iyy", iyy), ("Izz", izz)]:
        if val <= 0:
            raise URDFError(
                f"Postcondition violated: {body_name} {label}={val} not positive"
            )
    # Triangle inequality for principal inertias
    if ixx + iyy < izz or ixx + izz < iyy or iyy + izz < ixx:
        raise URDFError(
            f"Postcondition violated: {body_name} inertias "
            f"({ixx}, {iyy}, {izz}) violate triangle inequality"
        )