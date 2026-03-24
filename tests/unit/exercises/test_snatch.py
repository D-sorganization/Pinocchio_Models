"""Tests for snatch model builder."""

import math
import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.snatch.snatch_model import (
    SnatchModelBuilder,
    build_snatch_model,
)
from pinocchio_models.shared.constants import (
    SNATCH_ANKLE_ANGLE,
    SNATCH_HIP_ANGLE,
    SNATCH_KNEE_ANGLE,
)


class TestSnatchModelBuilder:
    def test_exercise_name(self) -> None:
        builder = SnatchModelBuilder()
        assert builder.exercise_name == "snatch"

    def test_build_produces_valid_urdf(self) -> None:
        xml_str = build_snatch_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "snatch"  # type: ignore

    def test_barbell_attached_to_both_hands(self) -> None:
        xml_str = build_snatch_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}  # type: ignore
        assert "barbell_to_hand_l" in joint_names
        assert "barbell_to_hand_r" in joint_names

    def test_body_count(self) -> None:
        xml_str = build_snatch_model()
        root = ET.fromstring(xml_str)
        links = root.findall("link")
        assert len(links) >= 18

    def test_joint_types(self) -> None:
        xml_str = build_snatch_model()
        root = ET.fromstring(xml_str)
        revolute = root.findall("joint[@type='revolute']")
        fixed = root.findall("joint[@type='fixed']")
        assert len(revolute) >= 14
        assert len(fixed) >= 3

    def test_wide_grip(self) -> None:
        """Snatch grip should be wider than deadlift grip."""
        builder = SnatchModelBuilder()
        assert builder.grip_offset_fraction > 0.4

    def test_initial_pose_sets_defaults(self) -> None:
        xml_str = build_snatch_model()
        root = ET.fromstring(xml_str)
        hip_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("hip_")  # type: ignore
        ]
        for j in hip_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                SNATCH_HIP_ANGLE, abs=1e-4
            )

    def test_initial_pose_knee_defaults(self) -> None:
        xml_str = build_snatch_model()
        root = ET.fromstring(xml_str)
        knee_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("knee_")  # type: ignore
        ]
        for j in knee_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                SNATCH_KNEE_ANGLE, abs=1e-4
            )

    def test_initial_pose_ankle_defaults(self) -> None:
        xml_str = build_snatch_model()
        root = ET.fromstring(xml_str)
        ankle_joints = [
            j
            for j in root.findall("joint")
            if j.get("name", "").startswith("ankle_")  # type: ignore
        ]
        for j in ankle_joints:
            assert j.get("initial_position") is not None  # type: ignore
            assert float(j.get("initial_position")) == pytest.approx(  # type: ignore
                SNATCH_ANKLE_ANGLE, abs=1e-4
            )

    def test_hip_angle_is_80_degrees(self) -> None:
        """Snatch setup: hips at 80 degrees flexion."""
        assert pytest.approx(math.radians(80.0), abs=1e-6) == SNATCH_HIP_ANGLE

    def test_hip_angle_within_limits(self) -> None:
        """Hip initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import HIP_FLEXION_MAX, HIP_FLEXION_MIN

        assert HIP_FLEXION_MIN <= SNATCH_HIP_ANGLE <= HIP_FLEXION_MAX

    def test_knee_angle_within_limits(self) -> None:
        """Knee initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import KNEE_FLEXION_MAX, KNEE_FLEXION_MIN

        assert KNEE_FLEXION_MIN <= SNATCH_KNEE_ANGLE <= KNEE_FLEXION_MAX

    def test_ankle_angle_within_limits(self) -> None:
        """Ankle initial angle must be within anatomical ROM."""
        from pinocchio_models.shared.constants import (
            ANKLE_FLEXION_MAX,
            ANKLE_FLEXION_MIN,
        )

        assert ANKLE_FLEXION_MIN <= SNATCH_ANKLE_ANGLE <= ANKLE_FLEXION_MAX

    def test_custom_body_parameters(self) -> None:
        xml_str = build_snatch_model(body_mass=70.0, height=1.65)
        root = ET.fromstring(xml_str)
        assert len(root.findall("link")) >= 18
