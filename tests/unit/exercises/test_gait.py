"""Tests for gait (walking) model builder."""

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.gait.gait_model import (
    GaitModelBuilder,
    build_gait_model,
)
from pinocchio_models.shared.constants import (
    GAIT_ANKLE_ANGLE,
    GAIT_HIP_ANGLE,
    GAIT_KNEE_ANGLE,
)


class TestGaitModelBuilder:
    def test_exercise_name(self) -> None:
        builder = GaitModelBuilder()
        assert builder.exercise_name == "gait"

    def test_build_produces_valid_urdf(self) -> None:
        xml_str = build_gait_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "gait"  # type: ignore

    def test_no_barbell_attached(self) -> None:
        """Gait model has no barbell attachment joints."""
        xml_str = build_gait_model()
        root = ET.fromstring(xml_str)
        joint_names = {j.get("name") for j in root.findall("joint")}  # type: ignore
        assert "barbell_to_hand_l" not in joint_names
        assert "barbell_to_hand_r" not in joint_names
        assert "barbell_to_torso" not in joint_names

    def test_has_body_links(self) -> None:
        xml_str = build_gait_model()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        # Body links should be present (pelvis, torso, legs, arms, etc.)
        link_names = {link.get("name") for link in links}  # type: ignore
        assert "pelvis" in link_names
        assert "torso" in link_names

    def test_initial_pose_hip_defaults(self) -> None:
        xml_str = build_gait_model()
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
                GAIT_HIP_ANGLE, abs=1e-4
            )

    def test_initial_pose_knee_defaults(self) -> None:
        xml_str = build_gait_model()
        root = ET.fromstring(xml_str)
        knee_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("knee_")  # type: ignore
        ]
        for j in knee_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                GAIT_KNEE_ANGLE, abs=1e-4
            )

    def test_initial_pose_ankle_defaults(self) -> None:
        xml_str = build_gait_model()
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
                GAIT_ANKLE_ANGLE, abs=1e-4
            )

    def test_custom_body_parameters(self) -> None:
        xml_str = build_gait_model(body_mass=65.0, height=1.60)
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert len(root.findall("link")) >= 20

    def test_hip_angle_within_limits(self) -> None:
        """Hip initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import (
            HIP_FLEXION_MAX,
            HIP_FLEXION_MIN,
        )

        assert HIP_FLEXION_MIN <= GAIT_HIP_ANGLE <= HIP_FLEXION_MAX
