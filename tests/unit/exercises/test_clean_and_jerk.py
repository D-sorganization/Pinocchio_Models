"""Tests for clean and jerk model builder."""

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.clean_and_jerk.clean_and_jerk_model import (
    CleanAndJerkModelBuilder,
    build_clean_and_jerk_model,
)


class TestCleanAndJerkModelBuilder:
    def test_exercise_name(self) -> None:
        builder = CleanAndJerkModelBuilder()
        assert builder.exercise_name == "clean_and_jerk"

    def test_build_produces_valid_urdf(self) -> None:
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "clean_and_jerk"

    def test_barbell_attached_to_both_hands(self) -> None:
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}
        assert "barbell_to_hand_l" in joint_names
        assert "barbell_to_hand_r" in joint_names

    def test_body_count(self) -> None:
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        assert len(links) >= 18

    def test_joint_types(self) -> None:
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        revolute = root.findall("joint[@type='revolute']")
        fixed = root.findall("joint[@type='fixed']")
        assert len(revolute) >= 14
        assert len(fixed) >= 3

    def test_initial_pose_sets_defaults(self) -> None:
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        hip_joints = [
            j for j in root.findall("joint") if j.get("name", "").startswith("hip_")
        ]
        for j in hip_joints:
            assert j.get("initial_position") is not None

    def test_custom_body_parameters(self) -> None:
        xml_str = build_clean_and_jerk_model(body_mass=90.0, height=1.80)
        root = ET.fromstring(xml_str)
        assert len(root.findall("link")) >= 18
