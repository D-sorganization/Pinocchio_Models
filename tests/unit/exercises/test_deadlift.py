"""Tests for deadlift model builder."""

import math
import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.deadlift.deadlift_model import (
    DeadliftModelBuilder,
    build_deadlift_model,
)
from pinocchio_models.shared.constants import (
    DEADLIFT_ANKLE_ANGLE,
    DEADLIFT_HIP_ANGLE,
    DEADLIFT_KNEE_ANGLE,
)


class TestDeadliftModelBuilder:
    def test_exercise_name(self) -> None:
        builder = DeadliftModelBuilder()
        assert builder.exercise_name == "deadlift"

    def test_build_produces_valid_urdf(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "deadlift"

    def test_barbell_attached_to_both_hands(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}
        assert "barbell_to_hand_l" in joint_names
        assert "barbell_to_hand_r" in joint_names

    def test_body_count(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        assert len(links) >= 18

    def test_joint_types(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        revolute = root.findall("joint[@type='revolute']")
        fixed = root.findall("joint[@type='fixed']")
        assert len(revolute) >= 14
        assert len(fixed) >= 3

    def test_barbell_attachment_is_fixed(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        for joint in root.findall("joint"):
            if joint.get("name") in ("barbell_to_hand_l", "barbell_to_hand_r"):
                assert joint.get("type") == "fixed"

    def test_initial_pose_sets_hip_defaults(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        hip_joints = [
            j for j in root.findall("joint") if j.get("name", "").startswith("hip_")
        ]
        for j in hip_joints:
            assert j.get("initial_position") is not None
            assert float(j.get("initial_position")) == pytest.approx(
                DEADLIFT_HIP_ANGLE, abs=1e-4
            )

    def test_initial_pose_sets_knee_defaults(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        knee_joints = [
            j for j in root.findall("joint") if j.get("name", "").startswith("knee_")
        ]
        for j in knee_joints:
            assert j.get("initial_position") is not None
            assert float(j.get("initial_position")) == pytest.approx(
                DEADLIFT_KNEE_ANGLE, abs=1e-4
            )

    def test_initial_pose_sets_ankle_defaults(self) -> None:
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        ankle_joints = [
            j for j in root.findall("joint") if j.get("name", "").startswith("ankle_")
        ]
        for j in ankle_joints:
            assert j.get("initial_position") is not None
            assert float(j.get("initial_position")) == pytest.approx(
                DEADLIFT_ANKLE_ANGLE, abs=1e-4
            )

    def test_hip_angle_is_80_degrees(self) -> None:
        """Deadlift setup: hips at 80 degrees flexion."""
        assert pytest.approx(math.radians(80.0), abs=1e-6) == DEADLIFT_HIP_ANGLE

    def test_hip_angle_within_limits(self) -> None:
        """Hip initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import HIP_FLEXION_MAX, HIP_FLEXION_MIN

        assert HIP_FLEXION_MIN <= DEADLIFT_HIP_ANGLE <= HIP_FLEXION_MAX

    def test_knee_angle_within_limits(self) -> None:
        """Knee initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import KNEE_FLEXION_MAX, KNEE_FLEXION_MIN

        assert KNEE_FLEXION_MIN <= DEADLIFT_KNEE_ANGLE <= KNEE_FLEXION_MAX

    def test_ankle_angle_within_limits(self) -> None:
        """Ankle initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import (
            ANKLE_FLEXION_MAX,
            ANKLE_FLEXION_MIN,
        )

        assert ANKLE_FLEXION_MIN <= DEADLIFT_ANKLE_ANGLE <= ANKLE_FLEXION_MAX

    def test_custom_body_parameters(self) -> None:
        xml_str = build_deadlift_model(body_mass=100.0, height=1.90)
        root = ET.fromstring(xml_str)
        assert len(root.findall("link")) >= 18
