"""Tests for sit-to-stand model builder."""

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.sit_to_stand.sit_to_stand_model import (
    SitToStandModelBuilder,
    build_sit_to_stand_model,
)
from pinocchio_models.shared.constants import (
    STS_ANKLE_ANGLE,
    STS_HIP_ANGLE,
    STS_KNEE_ANGLE,
)


class TestSitToStandModelBuilder:
    def test_exercise_name(self) -> None:
        builder = SitToStandModelBuilder()
        assert builder.exercise_name == "sit_to_stand"

    def test_build_produces_valid_urdf(self) -> None:
        xml_str = build_sit_to_stand_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "sit_to_stand"  # type: ignore

    def test_has_chair_body(self) -> None:
        """Sit-to-stand model should have a chair_seat link."""
        xml_str = build_sit_to_stand_model()
        root = ET.fromstring(xml_str)
        link_names = {link.get("name") for link in root.findall("link")}  # type: ignore
        assert "chair_seat" in link_names

    def test_chair_attached_to_pelvis(self) -> None:
        xml_str = build_sit_to_stand_model()
        root = ET.fromstring(xml_str)
        joint_names = {j.get("name") for j in root.findall("joint")}  # type: ignore
        assert "chair_to_world" in joint_names

    def test_chair_joint_is_fixed(self) -> None:
        xml_str = build_sit_to_stand_model()
        root = ET.fromstring(xml_str)
        for joint in root.findall("joint"):
            if joint.get("name") == "chair_to_world":
                assert joint.get("type") == "fixed"  # type: ignore

    def test_no_barbell_hand_attachment(self) -> None:
        """No barbell-to-hand joints in sit-to-stand."""
        xml_str = build_sit_to_stand_model()
        root = ET.fromstring(xml_str)
        joint_names = {j.get("name") for j in root.findall("joint")}  # type: ignore
        assert "barbell_to_hand_l" not in joint_names
        assert "barbell_to_hand_r" not in joint_names

    def test_initial_pose_hip_defaults(self) -> None:
        xml_str = build_sit_to_stand_model()
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
                STS_HIP_ANGLE, abs=1e-4
            )

    def test_initial_pose_knee_defaults(self) -> None:
        xml_str = build_sit_to_stand_model()
        root = ET.fromstring(xml_str)
        knee_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("knee_")  # type: ignore
        ]
        for j in knee_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                STS_KNEE_ANGLE, abs=1e-4
            )

    def test_initial_pose_ankle_defaults(self) -> None:
        xml_str = build_sit_to_stand_model()
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
                STS_ANKLE_ANGLE, abs=1e-4
            )

    def test_custom_body_parameters(self) -> None:
        xml_str = build_sit_to_stand_model(body_mass=60.0, height=1.65)
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert len(root.findall("link")) >= 20

    def test_hip_angle_within_limits(self) -> None:
        """Hip initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import (
            HIP_FLEXION_MAX,
            HIP_FLEXION_MIN,
        )

        assert HIP_FLEXION_MIN <= STS_HIP_ANGLE <= HIP_FLEXION_MAX
