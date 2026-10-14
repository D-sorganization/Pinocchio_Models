"""Tests for bench press model builder."""

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.bench_press.bench_press_model import (
    BenchPressModelBuilder,
    build_bench_press_model,
)
from pinocchio_models.shared.parity._canonical import conformance, spec

# Start pose of the generated model: the spec ``start`` via-pose (LIFT-3,
# UpstreamDrift#11743); coordinates the spec does not list are 0.
_START = spec.pose_coordinates(conformance.load_standard(), "bench_press", "start")
BENCH_PRESS_ELBOW_ANGLE = _START.get("elbow_l_flex", 0.0)
BENCH_PRESS_HIP_ANGLE = _START.get("hip_l_flex", 0.0)
BENCH_PRESS_KNEE_ANGLE = _START.get("knee_l_flex", 0.0)
BENCH_PRESS_SHOULDER_ANGLE = _START.get("shoulder_l_flex", 0.0)


class TestBenchPressModelBuilder:
    def test_exercise_name(self) -> None:
        builder = BenchPressModelBuilder()
        assert builder.exercise_name == "bench_press"

    def test_build_produces_valid_urdf(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "bench_press"  # type: ignore

    def test_barbell_attached_to_both_hands(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}  # type: ignore
        assert "barbell_to_hand_l" in joint_names
        assert "barbell_to_hand_r" in joint_names

    def test_body_count(self) -> None:
        """29 body + 3 barbell + 1 grip_r = 33 links minimum."""
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        assert len(links) >= 33

    def test_joint_types(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        revolute = root.findall("joint[@type='revolute']")
        fixed = root.findall("joint[@type='fixed']")
        assert len(revolute) >= 28
        assert len(fixed) >= 3  # barbell welds + hand attachments

    def test_barbell_attachment_is_fixed(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        for joint in root.findall("joint"):
            if joint.get("name") in ("barbell_to_hand_l", "barbell_to_hand_r"):  # type: ignore
                assert joint.get("type") == "fixed"  # type: ignore

    def test_xml_structure_has_robot_name(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        assert root.get("name") == "bench_press"  # type: ignore

    def test_initial_pose_sets_joint_defaults(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        shoulder_flex_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("shoulder_")
            and j.get("name", "").endswith("_flex")
        ]
        assert len(shoulder_flex_joints) == 2
        for j in shoulder_flex_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                BENCH_PRESS_SHOULDER_ANGLE, abs=1e-4
            )

    def test_initial_pose_elbow_defaults(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        elbow_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("elbow_")  # type: ignore
        ]
        for j in elbow_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                BENCH_PRESS_ELBOW_ANGLE, abs=1e-4
            )

    def test_initial_pose_hip_defaults(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        hip_flex_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("hip_")  # type: ignore
            and j.get("name", "").endswith("_flex")  # type: ignore
        ]
        assert len(hip_flex_joints) == 2
        for j in hip_flex_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                BENCH_PRESS_HIP_ANGLE, abs=1e-4
            )

    def test_initial_pose_knee_defaults(self) -> None:
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        knee_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("knee_")  # type: ignore
        ]
        for j in knee_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                BENCH_PRESS_KNEE_ANGLE, abs=1e-4
            )

    def test_custom_body_parameters(self) -> None:
        xml_str = build_bench_press_model(body_mass=100.0, height=1.90)
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        links = root.findall("link")
        assert len(links) >= 33

    def test_bench_mass_parity(self) -> None:
        """The bench mass is near-zero (1e-4 kg, borne by ground), matching cross-engine parity."""
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        bench_link = root.find(".//link[@name='bench']")
        assert bench_link is not None
        mass_elem = bench_link.find(".//inertial/mass")
        assert mass_elem is not None
        assert float(mass_elem.get("value", "0")) == pytest.approx(1e-4)
