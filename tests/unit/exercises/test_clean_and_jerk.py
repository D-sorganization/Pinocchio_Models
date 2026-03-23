"""Tests for clean and jerk model builder."""

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.clean_and_jerk.clean_and_jerk_model import (
    CleanAndJerkModelBuilder,
    build_clean_and_jerk_model,
)


class TestCleanAndJerkModelBuilder:
    def test_exercise_name(self):
        builder = CleanAndJerkModelBuilder()
        assert builder.exercise_name == "clean_and_jerk"

    def test_build_produces_valid_urdf(self):
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "clean_and_jerk"

    def test_barbell_attached_to_hand(self):
        xml_str = build_clean_and_jerk_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}
        assert "barbell_to_hand_l" in joint_names
