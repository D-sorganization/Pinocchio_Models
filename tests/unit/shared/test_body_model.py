"""Tests for full-body model generation (URDF format)."""

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.shared.body import BodyModelSpec, create_full_body


class TestBodyModelSpec:
    def test_defaults(self):
        spec = BodyModelSpec()
        assert spec.total_mass == 80.0
        assert spec.height == 1.75

    def test_rejects_zero_mass(self):
        with pytest.raises(ValueError, match="must be positive"):
            BodyModelSpec(total_mass=0.0)

    def test_rejects_negative_height(self):
        with pytest.raises(ValueError, match="must be positive"):
            BodyModelSpec(height=-1.0)

    def test_frozen(self):
        spec = BodyModelSpec()
        with pytest.raises(AttributeError):
            spec.total_mass = 90.0


class TestCreateFullBody:
    @pytest.fixture()
    def robot(self):
        return ET.Element("robot", name="test")

    def test_creates_pelvis(self, robot):
        links = create_full_body(robot)
        assert "pelvis" in links

    def test_creates_torso(self, robot):
        links = create_full_body(robot)
        assert "torso" in links

    def test_creates_bilateral_segments(self, robot):
        create_full_body(robot)
        link_names = {link.get("name") for link in robot.findall("link")}
        for segment in ["upper_arm", "forearm", "hand", "thigh", "shank", "foot"]:
            assert f"{segment}_l" in link_names
            assert f"{segment}_r" in link_names

    def test_minimum_link_count(self, robot):
        """15 body segments: pelvis, torso, head + 6 bilateral pairs."""
        create_full_body(robot)
        links = robot.findall("link")
        assert len(links) >= 15

    def test_all_masses_positive(self, robot):
        create_full_body(robot)
        for link in robot.findall("link"):
            mass_el = link.find("inertial/mass")
            mass = float(mass_el.get("value"))
            assert mass > 0, f"{link.get('name')} mass={mass}"

    def test_creates_revolute_joints(self, robot):
        create_full_body(robot)
        joints = robot.findall("joint[@type='revolute']")
        assert len(joints) >= 14

    def test_custom_spec(self, robot):
        spec = BodyModelSpec(total_mass=100.0, height=1.80)
        create_full_body(robot, spec)
        # Just verify it doesn't crash and produces links
        links = robot.findall("link")
        assert len(links) >= 15
