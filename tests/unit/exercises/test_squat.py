"""Tests for back squat model builder."""

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.squat.squat_model import (
    SquatModelBuilder,
    build_squat_model,
)
from pinocchio_models.shared.constants import (
    SQUAT_ANKLE_ANGLE,
    SQUAT_HIP_ANGLE,
    SQUAT_KNEE_ANGLE,
)


class TestSquatModelBuilder:
    def test_exercise_name(self) -> None:
        builder = SquatModelBuilder()
        assert builder.exercise_name == "back_squat"

    def test_build_produces_valid_urdf(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "back_squat"  # type: ignore

    def test_barbell_attached_to_torso(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}  # type: ignore
        assert "barbell_to_torso" in joint_names

    def test_barbell_not_attached_to_hands(self) -> None:
        """Squat attaches to torso, not hands."""
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        joint_names = {j.get("name") for j in root.findall("joint")}  # type: ignore
        assert "barbell_to_hand_l" not in joint_names
        assert "barbell_to_hand_r" not in joint_names

    def test_body_count(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        # 29 body + 3 barbell = 32 links minimum
        assert len(links) >= 32

    def test_joint_types(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        revolute = root.findall("joint[@type='revolute']")
        fixed = root.findall("joint[@type='fixed']")
        assert len(revolute) >= 28
        assert len(fixed) >= 3

    def test_torso_attachment_is_fixed(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        for joint in root.findall("joint"):
            if joint.get("name") == "barbell_to_torso":
                assert joint.get("type") == "fixed"  # type: ignore

    def test_initial_pose_sets_defaults(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        hip_flex_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("hip_")  # type: ignore
            and j.get("name", "").endswith("_flex")  # type: ignore
        ]
        assert len(hip_flex_joints) == 2  # bilateral
        for j in hip_flex_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                SQUAT_HIP_ANGLE, abs=1e-4
            )

    def test_initial_pose_knee_defaults(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        knee_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("knee_")  # type: ignore
        ]
        for j in knee_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                SQUAT_KNEE_ANGLE, abs=1e-4
            )

    def test_initial_pose_ankle_defaults(self) -> None:
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        ankle_flex_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("ankle_")  # type: ignore
            and j.get("name", "").endswith("_flex")  # type: ignore
        ]
        assert len(ankle_flex_joints) == 2  # bilateral
        for j in ankle_flex_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                SQUAT_ANKLE_ANGLE, abs=1e-4
            )

    def test_hip_angle_within_limits(self) -> None:
        """Hip initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import HIP_FLEXION_MAX, HIP_FLEXION_MIN

        assert HIP_FLEXION_MIN <= SQUAT_HIP_ANGLE <= HIP_FLEXION_MAX

    def test_custom_body_parameters(self) -> None:
        xml_str = build_squat_model(
            body_mass=100.0, height=1.90, plate_mass_per_side=80.0
        )
        root = ET.fromstring(xml_str)
        assert len(root.findall("link")) >= 32
