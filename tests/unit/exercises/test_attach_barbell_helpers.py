"""Unit tests for the ``attach_barbell`` decomposition on ``ExerciseModelBuilder``.

Introduced by the A-N Refresh 2026-04-14 batch (issue #133).  Covers the
two extracted static helpers plus the public orchestrator.
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.base import ExerciseConfig, ExerciseModelBuilder


class _MinimalBuilder(ExerciseModelBuilder):
    @property
    def exercise_name(self) -> str:
        return "minimal"

    def set_initial_pose(self, robot: ET.Element) -> None:
        return None


class _MalformedXmlBuilder(_MinimalBuilder):
    @property
    def exercise_name(self) -> str:
        return "malformed_xml"

    @property
    def uses_barbell(self) -> bool:
        return False

    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        # ElementTree will serialize this invalid element name, but the
        # post-serialization URDF validation must reject it before returning.
        ET.SubElement(robot, "bad tag")


def test_attach_shaft_to_left_hand_creates_two_fixed_joints_and_a_pivot() -> None:
    """Left-hand weld chains hand_l -> pivot -> barbell_shaft (issue #443).

    With zero abduction/tilt this reduces to the previous single
    fixed-offset weld: the pivot sits exactly at the old attachment point.
    """
    robot = ET.Element("robot")
    ExerciseModelBuilder._attach_shaft_to_left_hand(robot, grip_offset=0.3)
    links = robot.findall("link")
    assert len(links) == 1
    assert links[0].get("name") == "barbell_hand_l_pivot"

    joints = robot.findall("joint")
    assert len(joints) == 2
    j1, j2 = joints
    assert j1.get("name") == "barbell_to_hand_l"
    assert j1.get("type") == "fixed"
    assert j1.find("parent").get("link") == "hand_l"  # type: ignore[union-attr]
    assert j1.find("child").get("link") == "barbell_hand_l_pivot"  # type: ignore[union-attr]
    origin = j1.find("origin")
    assert origin is not None
    xyz = origin.get("xyz", "").split()
    # The left hand is at +y, so the shaft centre is -grip_offset from it.
    assert float(xyz[1]) == pytest.approx(-0.3)
    assert float(xyz[2]) == pytest.approx(0.0)
    assert origin.get("rpy", "").split() == ["0", "0", "0"]

    assert j2.get("name") == "barbell_hand_l_pivot_to_shaft"
    assert j2.get("type") == "fixed"
    assert j2.find("parent").get("link") == "barbell_hand_l_pivot"  # type: ignore[union-attr]
    assert j2.find("child").get("link") == "barbell_shaft"  # type: ignore[union-attr]
    origin2 = j2.find("origin")
    assert origin2 is not None
    assert origin2.get("xyz", "").split() == ["0", "0", "0"]
    assert origin2.get("rpy", "").split() == ["0", "0", "0"]


def test_attach_shaft_to_left_hand_cancels_abduction_and_tilt() -> None:
    """Nonzero abduction/tilt are reflected in the pivot's xyz/rpy exactly.

    This is the geometry that keeps the shaft level and centred when the
    arm is abducted to a wide grip (issue #443).
    """
    robot = ET.Element("robot")
    theta = math.radians(-30.0)
    phi = math.radians(10.0)
    ExerciseModelBuilder._attach_shaft_to_left_hand(
        robot, grip_offset=0.4, abduction_rad=theta, tilt_rad=phi
    )
    j1, j2 = robot.findall("joint")

    xyz = [float(v) for v in j1.find("origin").get("xyz", "").split()]  # type: ignore[union-attr]
    assert xyz == pytest.approx([0.0, -0.4 * math.cos(theta), -0.4 * math.sin(theta)])
    rpy = [float(v) for v in j1.find("origin").get("rpy", "").split()]  # type: ignore[union-attr]
    assert rpy == pytest.approx([theta, 0.0, 0.0])

    rpy2 = [float(v) for v in j2.find("origin").get("rpy", "").split()]  # type: ignore[union-attr]
    assert rpy2 == pytest.approx([0.0, -phi, 0.0])


def test_attach_virtual_grip_right_creates_link_and_joint() -> None:
    """Right-hand anchor is a zero-mass link fixed to the shaft at -grip_offset (right = -y)."""
    robot = ET.Element("robot")
    ExerciseModelBuilder._attach_virtual_grip_right(robot, grip_offset=0.3)
    # One new link and one new joint
    assert len(robot.findall("link")) == 1
    link = robot.find("link")
    assert link is not None
    assert link.get("name") == "barbell_grip_r"
    joints = robot.findall("joint")
    assert len(joints) == 1
    j = joints[0]
    assert j.get("name") == "barbell_to_hand_r"
    assert j.find("parent").get("link") == "barbell_shaft"  # type: ignore[union-attr]
    assert j.find("child").get("link") == "barbell_grip_r"  # type: ignore[union-attr]
    xyz = j.find("origin").get("xyz", "").split()  # type: ignore[union-attr]
    assert float(xyz[1]) == pytest.approx(-0.3)


def test_attach_barbell_orchestrates_both_helpers() -> None:
    """Public ``attach_barbell`` emits both weld-joints and the virtual link."""
    builder = _MinimalBuilder(ExerciseConfig())
    robot = ET.Element("robot")
    builder.attach_barbell(robot, body_links={}, barbell_links={})

    joint_names = {j.get("name") for j in robot.findall("joint")}
    assert {"barbell_to_hand_l", "barbell_to_hand_r"}.issubset(joint_names)
    link_names = {link.get("name") for link in robot.findall("link")}
    assert "barbell_grip_r" in link_names


def test_grip_offset_scales_linearly_with_fraction() -> None:
    """Snatch uses a wider grip; the y-offset scales with ``grip_offset_fraction``."""

    class WideGripBuilder(_MinimalBuilder):
        @property
        def grip_offset_fraction(self) -> float:
            return 0.45

    narrow = _MinimalBuilder(ExerciseConfig())
    wide = WideGripBuilder(ExerciseConfig())

    robot_n = ET.Element("robot")
    narrow.attach_barbell(robot_n, body_links={}, barbell_links={})
    robot_w = ET.Element("robot")
    wide.attach_barbell(robot_w, body_links={}, barbell_links={})

    def _left_y(robot: ET.Element) -> float:
        j = robot.find("joint[@name='barbell_to_hand_l']")
        assert j is not None
        origin = j.find("origin")
        assert origin is not None
        return float(origin.get("xyz", "").split()[1])

    assert abs(_left_y(robot_w)) > abs(_left_y(robot_n))


def test_build_rejects_malformed_serialized_xml() -> None:
    """Build must validate the serialized XML string before returning it."""
    builder = _MalformedXmlBuilder(ExerciseConfig())

    with pytest.raises(ValueError, match="not well-formed XML"):
        builder.build()
