"""Tests for deadlift model builder."""

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.deadlift.deadlift_model import (
    DeadliftModelBuilder,
    build_deadlift_model,
)
from pinocchio_models.shared.parity._canonical import conformance, spec

# Start pose of the generated model: the spec ``start`` via-pose (LIFT-3,
# UpstreamDrift#11743); coordinates the spec does not list are 0.
_START = spec.pose_coordinates(conformance.load_standard(), "deadlift", "start")
DEADLIFT_ANKLE_ANGLE = _START.get("ankle_l_flex", 0.0)
DEADLIFT_HIP_ANGLE = _START.get("hip_l_flex", 0.0)
DEADLIFT_KNEE_ANGLE = _START.get("knee_l_flex", 0.0)


class TestDeadliftModelBuilder:
    def test_exercise_name(self) -> None:
        builder = DeadliftModelBuilder()
        assert builder.exercise_name == "deadlift"

    def test_build_produces_valid_urdf(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "deadlift"  # type: ignore

    def test_barbell_attached_to_both_hands(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}  # type: ignore
        assert "barbell_to_hand_l" in joint_names
        assert "barbell_to_hand_r" in joint_names

    def test_body_count(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        # 29 body + 3 barbell + 1 grip_r = 33 links minimum
        assert len(links) >= 33

    def test_joint_types(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        revolute = root.findall("joint[@type='revolute']")
        fixed = root.findall("joint[@type='fixed']")
        assert len(revolute) >= 28
        assert len(fixed) >= 3

    def test_barbell_attachment_is_fixed(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        for joint in root.findall("joint"):
            if joint.get("name") in ("barbell_to_hand_l", "barbell_to_hand_r"):  # type: ignore
                assert joint.get("type") == "fixed"  # type: ignore

    def test_initial_pose_sets_hip_defaults(self) -> None:
        xml_str = build_deadlift_model()
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
                DEADLIFT_HIP_ANGLE, abs=1e-4
            )

    def test_initial_pose_sets_knee_defaults(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        knee_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("knee_")  # type: ignore
        ]
        for j in knee_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                DEADLIFT_KNEE_ANGLE, abs=1e-4
            )

    def test_initial_pose_sets_ankle_defaults(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        ankle_flex_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("ankle_")  # type: ignore
            and j.get("name", "").endswith("_flex")  # type: ignore
        ]
        assert len(ankle_flex_joints) == 2
        for j in ankle_flex_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                DEADLIFT_ANKLE_ANGLE, abs=1e-4
            )

    def test_custom_body_parameters(self) -> None:
        xml_str = build_deadlift_model(body_mass=100.0, height=1.90)
        root = ET.fromstring(xml_str)
        assert len(root.findall("link")) >= 33
