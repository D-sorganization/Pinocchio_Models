"""Tests for bench press model builder."""

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.bench_press.bench_press_model import (
    BenchPressModelBuilder,
    build_bench_press_model,
)


class TestBenchPressModelBuilder:
    def test_exercise_name(self):
        builder = BenchPressModelBuilder()
        assert builder.exercise_name == "bench_press"

    def test_build_produces_valid_urdf(self):
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        assert root.tag == "robot"
        assert root.get("name") == "bench_press"

    def test_barbell_attached_to_hand(self):
        xml_str = build_bench_press_model()
        root = ET.fromstring(xml_str)
        joints = root.findall("joint")
        joint_names = {j.get("name") for j in joints}
        assert "barbell_to_hand_l" in joint_names
