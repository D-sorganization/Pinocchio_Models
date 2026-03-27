"""Tests for clean and jerk model builder."""

import math
import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.clean_and_jerk.clean_and_jerk_model import (
    CleanAndJerkModelBuilder,
    build_clean_and_jerk_model,
)
from pinocchio_models.shared.constants import (
    CLEAN_AND_JERK_ANKLE_ANGLE,
    CLEAN_AND_JERK_HIP_ANGLE,
    CLEAN_AND_JERK_KNEE_ANGLE,
)


class TestCleanAndJerkModelBuilder:
    def test_exercise_name(self) -> None:
        builder = CleanAndJerkModelBuilder()
        assert builder.exercise_name == "clean_and_jerk"

    def test_build_produces_valid_urdf(self) -> None:
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "clean_and_jerk"  # type: ignore

    def test_barbell_attached_to_both_hands(self) -> None:
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}  # type: ignore
        assert "barbell_to_hand_l" in joint_names
        assert "barbell_to_hand_r" in joint_names

    def test_body_count(self) -> None:
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        assert len(links) >= 33

    def test_joint_types(self) -> None:
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        revolute = root.findall("joint[@type='revolute']")
        fixed = root.findall("joint[@type='fixed']")
        assert len(revolute) >= 28
        assert len(fixed) >= 3

    def test_initial_pose_sets_defaults(self) -> None:
        xml_str = build_clean_and_jerk_model()
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
                CLEAN_AND_JERK_HIP_ANGLE, abs=1e-4
            )

    def test_initial_pose_knee_defaults(self) -> None:
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        knee_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("knee_")  # type: ignore
        ]
        for j in knee_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                CLEAN_AND_JERK_KNEE_ANGLE, abs=1e-4
            )

    def test_initial_pose_ankle_defaults(self) -> None:
        xml_str = build_clean_and_jerk_model()
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
                CLEAN_AND_JERK_ANKLE_ANGLE, abs=1e-4
            )

    def test_hip_angle_is_75_degrees(self) -> None:
        """Clean-and-jerk setup: hips at 75 degrees flexion."""
        assert pytest.approx(math.radians(75.0), abs=1e-6) == CLEAN_AND_JERK_HIP_ANGLE

    def test_hip_angle_within_limits(self) -> None:
        """Hip initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import HIP_FLEXION_MAX, HIP_FLEXION_MIN

        assert HIP_FLEXION_MIN <= CLEAN_AND_JERK_HIP_ANGLE <= HIP_FLEXION_MAX

    def test_knee_angle_within_limits(self) -> None:
        """Knee initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import KNEE_FLEXION_MAX, KNEE_FLEXION_MIN

        assert KNEE_FLEXION_MIN <= CLEAN_AND_JERK_KNEE_ANGLE <= KNEE_FLEXION_MAX

    def test_ankle_angle_within_limits(self) -> None:
        """Ankle initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import (
            ANKLE_FLEXION_MAX,
            ANKLE_FLEXION_MIN,
        )

        assert ANKLE_FLEXION_MIN <= CLEAN_AND_JERK_ANKLE_ANGLE <= ANKLE_FLEXION_MAX

    def test_custom_body_parameters(self) -> None:
        xml_str = build_clean_and_jerk_model(body_mass=90.0, height=1.80)
        root = ET.fromstring(xml_str)
        assert len(root.findall("link")) >= 33
