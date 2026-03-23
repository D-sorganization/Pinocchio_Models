"""Tests for bench press model builder."""

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.bench_press.bench_press_model import (
    BenchPressModelBuilder,
    build_bench_press_model,
)


class TestBenchPressModelBuilder:
    def test_exercise_name(self) -> None:
        builder = BenchPressModelBuilder()
        assert builder.exercise_name == "bench_press"

    def test_build_produces_valid_urdf(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "bench_press"

    def test_barbell_attached_to_both_hands(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}
        assert "barbell_to_hand_l" in joint_names
        assert "barbell_to_hand_r" in joint_names

    def test_body_count(self) -> None:
        """15 body + 3 barbell = 18 links minimum."""
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        assert len(links) >= 18

    def test_joint_types(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        revolute = root.findall("joint[@type='revolute']")
        fixed = root.findall("joint[@type='fixed']")
        assert len(revolute) >= 14
        assert len(fixed) >= 3  # barbell welds + hand attachments

    def test_barbell_attachment_is_fixed(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        for joint in root.findall("joint"):
            if joint.get("name") in ("barbell_to_hand_l", "barbell_to_hand_r"):
                assert joint.get("type") == "fixed"

    def test_xml_structure_has_robot_name(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        assert root.get("name") == "bench_press"

    def test_initial_pose_sets_joint_defaults(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        shoulder_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("shoulder_")
        ]
        for j in shoulder_joints:
            assert j.get("initial_position") is not None

    def test_custom_body_parameters(self) -> None:
        xml_str = build_bench_press_model(body_mass=100.0, height=1.90)
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        links = root.findall("link")
        assert len(links) >= 18
