"""Tests for back squat model builder."""

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.squat.squat_model import (
    SquatModelBuilder,
    build_squat_model,
)


class TestSquatModelBuilder:
    def test_exercise_name(self) -> None:
        builder = SquatModelBuilder()
        assert builder.exercise_name == "back_squat"

    def test_build_produces_valid_urdf(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "back_squat"

    def test_barbell_attached_to_torso(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}
        assert "barbell_to_torso" in joint_names

    def test_barbell_not_attached_to_hands(self) -> None:
        """Squat attaches to torso, not hands."""
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        joint_names = {j.get("name") for j in root.findall("joint")}
        assert "barbell_to_hand_l" not in joint_names
        assert "barbell_to_hand_r" not in joint_names

    def test_body_count(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        assert len(links) >= 18

    def test_joint_types(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        revolute = root.findall("joint[@type='revolute']")
        fixed = root.findall("joint[@type='fixed']")
        assert len(revolute) >= 14
        assert len(fixed) >= 3

    def test_torso_attachment_is_fixed(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        for joint in root.findall("joint"):
            if joint.get("name") == "barbell_to_torso":
                assert joint.get("type") == "fixed"

    def test_initial_pose_sets_defaults(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        hip_joints = [
            j for j in root.findall("joint") if j.get("name", "").startswith("hip_")
        ]
        for j in hip_joints:
            assert j.get("initial_position") is not None

    def test_custom_body_parameters(self) -> None:
        xml_str = build_squat_model(
            body_mass=100.0, height=1.90, plate_mass_per_side=80.0
        )
        root = ET.fromstring(xml_str)
        assert len(root.findall("link")) >= 18
