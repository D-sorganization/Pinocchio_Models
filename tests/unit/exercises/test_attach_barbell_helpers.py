"""Unit tests for the ``attach_barbell`` decomposition on ``ExerciseModelBuilder``.

Introduced by the A-N Refresh 2026-04-14 batch (issue #133).  Covers the
two extracted static helpers plus the public orchestrator.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.base import ExerciseConfig, ExerciseModelBuilder


class _MinimalBuilder(ExerciseModelBuilder):
    @property
    def exercise_name(self) -> str:
        return "minimal"

    def set_initial_pose(self, robot: ET.Element) -> None:
        return None


def test_attach_shaft_to_left_hand_creates_single_fixed_joint() -> None:
    """Left-hand weld is a fixed joint from hand_l to barbell_shaft."""
    robot = ET.Element("robot")
    ExerciseModelBuilder._attach_shaft_to_left_hand(robot, grip_offset=0.3)
    joints = robot.findall("joint")
    assert len(joints) == 1
    j = joints[0]
    assert j.get("name") == "barbell_to_hand_l"
    assert j.get("type") == "fixed"
    assert j.find("parent").get("link") == "hand_l"  # type: ignore[union-attr]
    assert j.find("child").get("link") == "barbell_shaft"  # type: ignore[union-attr]
    origin = j.find("origin")
    assert origin is not None
    xyz = origin.get("xyz", "").split()
    # y offset equals -grip_offset (left side is at -y)
    assert float(xyz[1]) < 0


def test_attach_virtual_grip_right_creates_link_and_joint() -> None:
    """Right-hand anchor is a zero-mass link fixed to the shaft at +2*grip_offset."""
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
