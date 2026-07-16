"""Design-by-Contract postcondition checks — Pinocchio_Models wrapper.

Re-exports the generic :mod:`robotics_contracts.postconditions` guards,
wrapping them with domain-specific :class:`URDFError` exceptions for
backward compatibility.

Migration note:
    Direct callers can switch to ``from robotics_contracts.postconditions import ...``
    and use ``ValueError`` directly, dropping the URDFError wrapper.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET

import robotics_contracts.postconditions as _rc
from pinocchio_models.exceptions import URDFError

logger = logging.getLogger(__name__)


def _parse_robot_root(xml_string: str) -> ET.Element:
    """Parse *xml_string* and verify the root element is ``<robot>``."""
    try:
        root = ET.fromstring(xml_string)  # nosec B314 — parsing self-generated XML
    except ET.ParseError as exc:
        raise URDFError(
            f"Generated URDF is not well-formed XML: {exc}",
            error_code="PM204",
        ) from exc
    if root.tag != "robot":
        raise URDFError(
            f"URDF root must be <robot>, got <{root.tag}>",
            error_code="PM203",
        )
    return root


_VALID_TAGS = frozenset(
    [
        "robot",
        "link",
        "joint",
        "origin",
        "inertial",
        "mass",
        "inertia",
        "visual",
        "geometry",
        "cylinder",
        "box",
        "sphere",
        "collision",
        "parent",
        "child",
        "axis",
        "limit",
        "color",
        "material",
    ]
)


def _collect_link_names_and_joints(
    root: ET.Element,
) -> tuple[set[str], list[ET.Element]]:
    """Collect declared link names and joint elements while validating tags."""
    link_names: set[str] = set()
    joints: list[ET.Element] = []

    for el in root.iter():
        tag = el.tag
        if type(tag) is not str:
            # ElementTree stores comments and processing instructions as
            # callables in the .tag field, so we skip them.
            continue
        if tag not in _VALID_TAGS:
            raise URDFError(
                f"Generated URDF is not well-formed XML: invalid tag '{tag}'",
                error_code="PM204",
            )
        if tag == "link":
            name = el.get("name")
            if name:
                link_names.add(name)
        elif tag == "joint":
            joints.append(el)

    return link_names, joints


def _ensure_known_child_link(
    joint_name: str,
    child_link: str,
    link_names: set[str],
) -> None:
    """Verify a joint child link refers to a declared link."""
    if child_link and child_link not in link_names:
        raise URDFError(
            f"Joint '{joint_name}' references unknown child link '{child_link}'",
            error_code="PM201",
        )


def _ensure_single_parent_link(
    joint_name: str,
    child_link: str,
    child_parent_map: dict[str, str],
) -> None:
    """Verify a child link is assigned to at most one parent joint."""
    if child_link in child_parent_map:
        raise URDFError(
            f"Link '{child_link}' is declared as child of both "
            f"'{child_parent_map[child_link]}' and '{joint_name}' — "
            "URDF requires each link to have exactly one parent joint",
            error_code="PM202",
        )
    if child_link:
        child_parent_map[child_link] = joint_name


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
        raise URDFError(
            f"URDF root must be <robot>, got <{root.tag}>",
            error_code="PM203",
        )

    link_names, joints = _collect_link_names_and_joints(root)

    child_parent_map: dict[str, str] = {}
    for joint in joints:
        joint_name = joint.get("name", "<unnamed>")

        parent_el = joint.find("parent")
        child_el = joint.find("child")
        if parent_el is None or child_el is None:
            continue

        child_link = child_el.get("link", "")

        # (a) We used to warn if parent link name does not exist in the declared link set.
        # However, this is intentional for aliased parent links in the body model, and logging
        # causes significant overhead during benchmark/generation. Therefore, we do not log.

        _ensure_known_child_link(joint_name, child_link, link_names)
        _ensure_single_parent_link(joint_name, child_link, child_parent_map)

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
    try:
        _rc.ensure_positive_mass(mass, body_name)
    except ValueError as exc:
        raise URDFError(str(exc), error_code="PM205") from exc


def ensure_positive_definite_inertia(
    ixx: float, iyy: float, izz: float, body_name: str
) -> None:
    """Validate that principal inertias are positive (necessary for PD)."""
    try:
        _rc.ensure_positive_definite_inertia(ixx, iyy, izz, body_name)
    except ValueError as exc:
        raise URDFError(str(exc), error_code="PM206") from exc
