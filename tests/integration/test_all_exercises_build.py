"""Integration tests: verify all five exercise models build end-to-end.

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
from pinocchio_models.exercises.snatch.snatch_model import build_snatch_model
from pinocchio_models.exercises.squat.squat_model import build_squat_model

ALL_BUILDERS = [
    ("back_squat", build_squat_model),
    ("bench_press", build_bench_press_model),
    ("deadlift", build_deadlift_model),
    ("snatch", build_snatch_model),
    ("clean_and_jerk", build_clean_and_jerk_model),
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
        """Every exercise should have at least 18 links (15 body + 3 barbell)."""
        xml_str = builder()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        assert len(links) >= 18

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
        "name,builder", ALL_BUILDERS, ids=[n for n, _ in ALL_BUILDERS]
    )
    def test_barbell_present(self, name: Any, builder: Any) -> None:
        xml_str = builder()
        root = ET.fromstring(xml_str)
        link_names = {ln.get("name") for ln in root.findall("link")}  # type: ignore
        assert "barbell_shaft" in link_names
        assert "barbell_left_sleeve" in link_names
        assert "barbell_right_sleeve" in link_names
