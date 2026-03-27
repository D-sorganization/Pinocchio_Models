"""Integration tests: verify all seven exercise models build end-to-end.

Each model must produce well-formed URDF XML with the correct structure:
<robot name="exercise_name"> with links and joints.
"""

import xml.etree.ElementTree as ET
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

ALL_BUILDERS = [
    ("back_squat", build_squat_model),
    ("bench_press", build_bench_press_model),
    ("deadlift", build_deadlift_model),
    ("snatch", build_snatch_model),
    ("clean_and_jerk", build_clean_and_jerk_model),
    ("gait", build_gait_model),
    ("sit_to_stand", build_sit_to_stand_model),
]


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
        assert root.get("name") == name  # type: ignore

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
            mass = float(mass_el.get("value"))  # type: ignore
            assert mass > 0, f"{link.get('name')} mass={mass}"  # type: ignore

    @pytest.mark.parametrize(
        "name,builder",
        [b for b in ALL_BUILDERS if b[0] in _BARBELL_EXERCISES],
        ids=[n for n, _ in ALL_BUILDERS if n in _BARBELL_EXERCISES],
    )
    def test_barbell_present(self, name: Any, builder: Any) -> None:
        """Only barbell exercises should contain barbell links."""
        xml_str = builder()
        root = ET.fromstring(xml_str)
        link_names = {ln.get("name") for ln in root.findall("link")}  # type: ignore
        assert "barbell_shaft" in link_names
        assert "barbell_left_sleeve" in link_names
        assert "barbell_right_sleeve" in link_names

    @pytest.mark.parametrize(
        "name,builder",
        [b for b in ALL_BUILDERS if b[0] not in _BARBELL_EXERCISES],
        ids=[n for n, _ in ALL_BUILDERS if n not in _BARBELL_EXERCISES],
    )
    def test_no_barbell_for_bodyweight(self, name: Any, builder: Any) -> None:
        """Bodyweight exercises must not contain barbell links."""
        xml_str = builder()
        root = ET.fromstring(xml_str)
        link_names = {ln.get("name") for ln in root.findall("link")}  # type: ignore
        assert "barbell_shaft" not in link_names
