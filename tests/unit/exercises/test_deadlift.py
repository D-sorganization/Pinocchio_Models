"""Tests for deadlift model builder."""

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.deadlift.deadlift_model import (
    DeadliftModelBuilder,
    build_deadlift_model,
)


class TestDeadliftModelBuilder:
    def test_exercise_name(self):
        builder = DeadliftModelBuilder()
        assert builder.exercise_name == "deadlift"

    def test_build_produces_valid_urdf(self):
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "deadlift"

    def test_barbell_attached_to_hand(self):
        xml_str = build_deadlift_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}
        assert "barbell_to_hand_l" in joint_names
