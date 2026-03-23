"""Tests for back squat model builder."""

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.squat.squat_model import (
    SquatModelBuilder,
    build_squat_model,
)


class TestSquatModelBuilder:
    def test_exercise_name(self):
        builder = SquatModelBuilder()
        assert builder.exercise_name == "back_squat"

    def test_build_produces_valid_urdf(self):
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "back_squat"

    def test_barbell_attached_to_torso(self):
        xml_str = build_squat_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}
        assert "barbell_to_torso" in joint_names
