"""Tests for snatch model builder."""

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.snatch.snatch_model import (
    SnatchModelBuilder,
    build_snatch_model,
)


class TestSnatchModelBuilder:
    def test_exercise_name(self):
        builder = SnatchModelBuilder()
        assert builder.exercise_name == "snatch"

    def test_build_produces_valid_urdf(self):
        xml_str = build_snatch_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "snatch"

    def test_barbell_attached_to_hand(self):
        xml_str = build_snatch_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}
        assert "barbell_to_hand_l" in joint_names
