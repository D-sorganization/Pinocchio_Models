"""Integration tests: verify all seven exercise models build end-to-end.

Each model must produce well-formed URDF XML with the correct structure:
<robot name="exercise_name"> with links and joints.
"""

import xml.etree.ElementTree as ET
from collections.abc import Callable
from typing import Any

import pytest

from pinocchio_models.exercises.bench_press.bench_press_model import (
    build_bench_press_model,
)
from pinocchio_models.exercises.clean_and_jerk.clean_and_jerk_model import (
    build_clean_and_jerk_model,
)
from pinocchio_models.exercises.deadlift.deadlift_model import build_deadlift_model
from pinocchio_models.exercises.gait.gait_model import build_gait_model
from pinocchio_models.exercises.sit_to_stand.sit_to_stand_model import (
    build_sit_to_stand_model,
)
from pinocchio_models.exercises.snatch.snatch_model import build_snatch_model
from pinocchio_models.exercises.squat.squat_model import build_squat_model

# Exercises that include a barbell in the URDF.
_BARBELL_EXERCISES: frozenset[str] = frozenset(
    {"back_squat", "bench_press", "deadlift", "snatch", "clean_and_jerk"}
)

ALL_BUILDERS: list[tuple[str, Callable[[], str]]] = [
    ("back_squat", build_squat_model),
    ("bench_press", build_bench_press_model),
    ("deadlift", build_deadlift_model),
    ("snatch", build_snatch_model),
    ("clean_and_jerk", build_clean_and_jerk_model),
    ("gait", build_gait_model),
    ("sit_to_stand", build_sit_to_stand_model),
]


def _link_names(root: ET.Element) -> set[str]:
    """Extract all link names from a URDF root element."""
    return {name for el in root.findall("link") if (name := el.get("name")) is not None}


class TestAllExercisesBuild:
    @pytest.mark.parametrize(
        "name,builder", ALL_BUILDERS, ids=[n for n, _ in ALL_BUILDERS]
    )
    def test_produces_valid_urdf(self, name: Any, builder: Any) -> None:
        xml_str = builder()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"

    @pytest.mark.parametrize(
        "name,builder", ALL_BUILDERS, ids=[n for n, _ in ALL_BUILDERS]
    )
    def test_model_name_matches(self, name: Any, builder: Any) -> None:
        xml_str = builder()
        root = ET.fromstring(xml_str)
        assert root.get("name") == name

    @pytest.mark.parametrize(
        "name,builder", ALL_BUILDERS, ids=[n for n, _ in ALL_BUILDERS]
    )
    def test_has_links_and_joints(self, name: Any, builder: Any) -> None:
        xml_str = builder()
        root = ET.fromstring(xml_str)
        assert len(root.findall("link")) > 0
        assert len(root.findall("joint")) > 0

    @pytest.mark.parametrize(
        "name,builder", ALL_BUILDERS, ids=[n for n, _ in ALL_BUILDERS]
    )
    def test_minimum_link_count(self, name: Any, builder: Any) -> None:
        """Barbell exercises need >= 32 links (29 body + 3 barbell).

        Non-barbell exercises need >= 29 links (body only).
        """
        xml_str = builder()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        if name in _BARBELL_EXERCISES:
            assert len(links) >= 32
        else:
            assert len(links) >= 29

    @pytest.mark.parametrize(
        "name,builder", ALL_BUILDERS, ids=[n for n, _ in ALL_BUILDERS]
    )
    def test_all_masses_positive(self, name: Any, builder: Any) -> None:
        xml_str = builder()
        root = ET.fromstring(xml_str)
        for link in root.findall("link"):
            mass_el = link.find("inertial/mass")
            assert mass_el is not None, f"Link {link.get('name')} missing mass"
            mass_val = mass_el.get("value")
            assert mass_val is not None
            mass = float(mass_val)
            link_name = link.get("name", "<unnamed>")
            assert mass > 0, f"{link_name} mass={mass}"

    @pytest.mark.parametrize(
        "name,builder",
        [b for b in ALL_BUILDERS if b[0] in _BARBELL_EXERCISES],
        ids=[n for n, _ in ALL_BUILDERS if n in _BARBELL_EXERCISES],
    )
    def test_barbell_present(self, name: Any, builder: Any) -> None:
        """Only barbell exercises should contain barbell links."""
        xml_str = builder()
        root = ET.fromstring(xml_str)
        link_set = _link_names(root)
        assert "barbell_shaft" in link_set
        assert "barbell_left_sleeve" in link_set
        assert "barbell_right_sleeve" in link_set

    @pytest.mark.parametrize(
        "name,builder",
        [b for b in ALL_BUILDERS if b[0] not in _BARBELL_EXERCISES],
        ids=[n for n, _ in ALL_BUILDERS if n not in _BARBELL_EXERCISES],
    )
    def test_no_barbell_for_bodyweight(self, name: Any, builder: Any) -> None:
        """Bodyweight exercises must not contain barbell links."""
        xml_str = builder()
        root = ET.fromstring(xml_str)
        link_set = _link_names(root)
        assert "barbell_shaft" not in link_set


class TestGaitIntegration:
    """Integration tests for gait model (issue #77)."""

    def test_gait_builds_successfully(self) -> None:
        """Gait model builds and produces valid URDF."""
        xml_str = build_gait_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "gait"

    def test_gait_has_no_barbell(self) -> None:
        """Gait is a bodyweight exercise with no barbell."""
        xml_str = build_gait_model()
        root = ET.fromstring(xml_str)
        link_set = _link_names(root)
        assert "barbell_shaft" not in link_set

    def test_gait_has_bilateral_legs(self) -> None:
        """Gait model must have both left and right leg segments."""
        xml_str = build_gait_model()
        root = ET.fromstring(xml_str)
        link_set = _link_names(root)
        for side in ("l", "r"):
            assert f"thigh_{side}" in link_set
            assert f"shank_{side}" in link_set
            assert f"foot_{side}" in link_set

    def test_gait_foot_collision_geometry(self) -> None:
        """Gait model feet should have collision geometry for ground contact."""
        xml_str = build_gait_model()
        root = ET.fromstring(xml_str)
        for side in ("l", "r"):
            foot = root.find(f".//link[@name='foot_{side}']")
            assert foot is not None, f"foot_{side} link missing"
            collision = foot.find("collision")
            assert collision is not None, f"foot_{side} missing collision geometry"


class TestSitToStandIntegration:
    """Integration tests for sit-to-stand model (issue #77)."""

    def test_sit_to_stand_builds_successfully(self) -> None:
        """Sit-to-stand model builds and produces valid URDF."""
        xml_str = build_sit_to_stand_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "sit_to_stand"

    def test_sit_to_stand_has_no_barbell(self) -> None:
        """Sit-to-stand is a bodyweight exercise with no barbell."""
        xml_str = build_sit_to_stand_model()
        root = ET.fromstring(xml_str)
        link_set = _link_names(root)
        assert "barbell_shaft" not in link_set

    def test_sit_to_stand_has_chair_fixture(self) -> None:
        """Sit-to-stand model should have a chair fixture link."""
        xml_str = build_sit_to_stand_model()
        root = ET.fromstring(xml_str)
        link_set = _link_names(root)
        # Chair fixture is expected for sit-to-stand
        assert "chair_seat" in link_set

    def test_sit_to_stand_has_full_body(self) -> None:
        """Sit-to-stand model must have core body segments."""
        xml_str = build_sit_to_stand_model()
        root = ET.fromstring(xml_str)
        link_set = _link_names(root)
        assert "pelvis" in link_set
        assert "torso" in link_set
        assert "head" in link_set
