"""Unit tests for the bilateral-limb helpers in body_anthropometrics.py.

Covers the decomposition of ``_add_bilateral_limb_simple`` introduced by
A-N Refresh 2026-04-14 (issue #133).
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.shared.body.body_anthropometrics import (
    BodyModelSpec,
    _add_bilateral_limb_simple,
    _add_limb_side_simple,
    _resolve_bilateral_parent,
    _seg,
)
from pinocchio_models.shared.utils.geometry import cylinder_inertia


def test_resolve_bilateral_parent_uses_side_suffix_for_limbs() -> None:
    """Bilateral segments get a side-specific parent name."""
    assert _resolve_bilateral_parent("thigh", "l") == "thigh_l"
    assert _resolve_bilateral_parent("thigh", "r") == "thigh_r"


def test_resolve_bilateral_parent_leaves_central_segments_unchanged() -> None:
    """Pelvis / torso / head are central and must not gain a suffix."""
    assert _resolve_bilateral_parent("pelvis", "l") == "pelvis"
    assert _resolve_bilateral_parent("torso", "r") == "torso"
    assert _resolve_bilateral_parent("head", "l") == "head"


def test_add_limb_side_simple_emits_link_and_joint() -> None:
    """One-side helper emits exactly one link and one revolute joint."""
    robot = ET.Element("robot")
    spec = BodyModelSpec()
    mass, length, radius = _seg(spec, "shank")
    inertia = cylinder_inertia(mass, radius, length)

    _add_limb_side_simple(
        robot,
        side="l",
        sign=-1.0,
        seg_name="shank",
        parent_name="thigh",
        mass=mass,
        length=length,
        radius=radius,
        inertia=inertia,
        parent_offset_z=-length,
        parent_lateral_y=0.05,
        coord_prefix="knee",
        range_min=-2.0,
        range_max=0.0,
    )

    links = robot.findall("link")
    joints = robot.findall("joint")
    assert len(links) == 1
    assert links[0].get("name") == "shank_l"
    assert len(joints) == 1
    j = joints[0]
    assert j.get("name") == "knee_l"
    assert j.find("parent").get("link") == "thigh_l"  # type: ignore[union-attr]
    # Left side: y offset is negative.
    xyz = j.find("origin").get("xyz", "").split()  # type: ignore[union-attr]
    assert float(xyz[1]) < 0


def test_add_bilateral_limb_simple_creates_both_sides() -> None:
    """Both left and right limbs are created, with matching joint names."""
    robot = ET.Element("robot")
    _add_bilateral_limb_simple(
        robot,
        BodyModelSpec(),
        seg_name="shank",
        parent_name="thigh",
        parent_offset_z=-0.4,
        parent_lateral_y=0.05,
        coord_prefix="knee",
        range_min=-2.0,
        range_max=0.0,
    )
    link_names = {link.get("name") for link in robot.findall("link")}
    joint_names = {j.get("name") for j in robot.findall("joint")}
    assert {"shank_l", "shank_r"}.issubset(link_names)
    assert {"knee_l", "knee_r"}.issubset(joint_names)


def test_add_bilateral_limb_simple_symmetric_y_offset() -> None:
    """Left joint has negative y origin; right joint has positive y origin."""
    robot = ET.Element("robot")
    _add_bilateral_limb_simple(
        robot,
        BodyModelSpec(),
        seg_name="shank",
        parent_name="thigh",
        parent_offset_z=-0.4,
        parent_lateral_y=0.05,
        coord_prefix="knee",
        range_min=-2.0,
        range_max=0.0,
    )
    left = robot.find("joint[@name='knee_l']")
    right = robot.find("joint[@name='knee_r']")
    assert left is not None and right is not None
    lxyz = left.find("origin").get("xyz", "").split()  # type: ignore[union-attr]
    rxyz = right.find("origin").get("xyz", "").split()  # type: ignore[union-attr]
    assert float(lxyz[1]) == pytest.approx(-float(rxyz[1]))
