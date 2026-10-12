"""Unit tests for the spec-driven barbell weld of ``SpecLiftBuilder``.

Introduced by the A-N Refresh 2026-04-14 batch (issue #133); since LIFT-3
(UpstreamDrift#11743) the weld places the bar where the spec ``start`` via-pose
puts it, in the left hand's frame, instead of deriving it from a grip fraction.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.base import ExerciseConfig
from pinocchio_models.exercises.spec_lift import SpecLiftBuilder


class _MinimalBuilder(SpecLiftBuilder):
    @property
    def exercise_name(self) -> str:
        return "minimal"

    @property
    def spec_exercise(self) -> str:
        return "deadlift"


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


def _origin(joint: ET.Element) -> tuple[list[float], list[float]]:
    origin = joint.find("origin")
    assert origin is not None
    return (
        [float(v) for v in origin.get("xyz", "").split()],
        [float(v) for v in origin.get("rpy", "").split()],
    )


def test_attach_barbell_welds_the_shaft_to_hand_l_at_the_spec_start() -> None:
    builder = _MinimalBuilder(ExerciseConfig())
    robot = ET.Element("robot")
    builder.attach_barbell(robot, body_links={}, barbell_links={})

    weld = robot.find("joint[@name='barbell_to_hand_l']")
    assert weld is not None
    assert weld.get("type") == "fixed"
    assert weld.find("parent").get("link") == "hand_l"  # type: ignore[union-attr]
    assert weld.find("child").get("link") == "barbell_shaft"  # type: ignore[union-attr]
    xyz, rpy = _origin(weld)
    want_xyz, want_rpy = builder.spec_start.bar_in("hand_l")
    # URDF numbers are serialised to 6 decimals (``float_str``).
    assert xyz == pytest.approx(list(want_xyz), abs=1e-6)
    assert rpy == pytest.approx(list(want_rpy), abs=1e-6)


def test_attach_barbell_adds_the_right_grip_anchor_at_the_spec_width() -> None:
    """Right-hand anchor: zero-mass link on the shaft at -grip half width."""
    builder = _MinimalBuilder(ExerciseConfig())
    robot = ET.Element("robot")
    builder.attach_barbell(robot, body_links={}, barbell_links={})

    link = robot.find("link[@name='barbell_grip_r']")
    assert link is not None
    anchor = robot.find("joint[@name='barbell_to_hand_r']")
    assert anchor is not None
    assert anchor.find("parent").get("link") == "barbell_shaft"  # type: ignore[union-attr]
    assert anchor.find("child").get("link") == "barbell_grip_r"  # type: ignore[union-attr]
    xyz, _ = _origin(anchor)
    assert xyz == pytest.approx([0.0, -0.45 / 2.0, 0.0])  # spec deadlift width


def test_grip_anchor_follows_the_spec_grip_width() -> None:
    """Snatch (0.9 m) holds the bar wider than the deadlift (0.45 m)."""

    class _Snatch(_MinimalBuilder):
        @property
        def spec_exercise(self) -> str:
            return "snatch"

    def _right_y(builder: SpecLiftBuilder) -> float:
        robot = ET.Element("robot")
        builder.attach_barbell(robot, body_links={}, barbell_links={})
        anchor = robot.find("joint[@name='barbell_to_hand_r']")
        assert anchor is not None
        return _origin(anchor)[0][1]

    narrow = _right_y(_MinimalBuilder(ExerciseConfig()))
    wide = _right_y(_Snatch(ExerciseConfig()))
    assert abs(wide) > abs(narrow)


def test_build_rejects_malformed_serialized_xml() -> None:
    """Build must validate the serialized XML string before returning it."""
    builder = _MalformedXmlBuilder(ExerciseConfig())

    with pytest.raises(ValueError, match="not well-formed XML"):
        builder.build()
