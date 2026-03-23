"""Tests for barbell model generation (URDF format)."""

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.shared.barbell import BarbellSpec, create_barbell_links


class TestBarbellSpec:
    def test_mens_defaults(self):
        spec = BarbellSpec.mens_olympic()
        assert spec.total_length == 2.20
        assert spec.bar_mass == 20.0
        assert spec.shaft_diameter == 0.028
        assert spec.plate_mass_per_side == 0.0

    def test_womens_defaults(self):
        spec = BarbellSpec.womens_olympic()
        assert spec.total_length == 2.01
        assert spec.bar_mass == 15.0
        assert spec.shaft_diameter == 0.025

    def test_sleeve_length(self):
        spec = BarbellSpec.mens_olympic()
        expected = (2.20 - 1.31) / 2.0
        assert spec.sleeve_length == pytest.approx(expected)

    def test_total_mass_with_plates(self):
        spec = BarbellSpec.mens_olympic(plate_mass_per_side=60.0)
        assert spec.total_mass == pytest.approx(140.0)

    def test_shaft_mass_proportional(self):
        spec = BarbellSpec.mens_olympic()
        assert spec.shaft_mass == pytest.approx(20.0 * 1.31 / 2.20)

    def test_rejects_negative_plate_mass(self):
        with pytest.raises(ValueError, match="non-negative"):
            BarbellSpec(plate_mass_per_side=-1.0)

    def test_rejects_shaft_longer_than_total(self):
        with pytest.raises(ValueError, match="shaft_length"):
            BarbellSpec(total_length=1.0, shaft_length=1.5)

    def test_rejects_zero_diameter(self):
        with pytest.raises(ValueError, match="must be positive"):
            BarbellSpec(shaft_diameter=0.0)

    def test_frozen(self):
        spec = BarbellSpec.mens_olympic()
        with pytest.raises(AttributeError):
            spec.bar_mass = 25.0


class TestCreateBarbellLinks:
    @pytest.fixture()
    def robot(self):
        return ET.Element("robot", name="test")

    def test_creates_three_links(self, robot):
        spec = BarbellSpec.mens_olympic()
        links = create_barbell_links(robot, spec)
        assert len(links) == 3
        assert "barbell_shaft" in links
        assert "barbell_left_sleeve" in links
        assert "barbell_right_sleeve" in links

    def test_creates_two_fixed_joints(self, robot):
        spec = BarbellSpec.mens_olympic()
        create_barbell_links(robot, spec)
        joints = robot.findall("joint[@type='fixed']")
        assert len(joints) == 2

    def test_custom_prefix(self, robot):
        spec = BarbellSpec.mens_olympic()
        links = create_barbell_links(robot, spec, prefix="bar")
        assert "bar_shaft" in links

    def test_mass_conservation(self, robot):
        spec = BarbellSpec.mens_olympic(plate_mass_per_side=50.0)
        create_barbell_links(robot, spec)
        total = sum(
            float(link.find("inertial/mass").get("value"))
            for link in robot.findall("link")
        )
        assert total == pytest.approx(spec.total_mass, rel=1e-4)
