"""Tests for clean and jerk model builder."""

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.clean_and_jerk.clean_and_jerk_model import (
    CleanAndJerkModelBuilder,
    build_clean_and_jerk_model,
)
from pinocchio_models.shared.parity._canonical import conformance, spec

# Start pose of the generated model: the spec ``start`` via-pose (LIFT-3,
# UpstreamDrift#11743); coordinates the spec does not list are 0.
_START = spec.pose_coordinates(conformance.load_standard(), "clean_and_jerk", "start")
CLEAN_AND_JERK_ANKLE_ANGLE = _START.get("ankle_l_flex", 0.0)
CLEAN_AND_JERK_HIP_ANGLE = _START.get("hip_l_flex", 0.0)
CLEAN_AND_JERK_KNEE_ANGLE = _START.get("knee_l_flex", 0.0)


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

    def test_custom_body_parameters(self) -> None:
        xml_str = build_clean_and_jerk_model(body_mass=90.0, height=1.80)
        root = ET.fromstring(xml_str)
        assert len(root.findall("link")) >= 33
