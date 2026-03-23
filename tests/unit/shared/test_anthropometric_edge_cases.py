"""Edge-case anthropometric tests for body model generation."""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.shared.body import BodyModelSpec, create_full_body


class TestAnthropometricEdgeCases:
    def test_very_small_person(self) -> None:
        """A very small person (child-sized) should still produce valid URDF."""
        spec = BodyModelSpec(total_mass=25.0, height=1.00)
        robot = ET.Element("robot", name="test")
        links = create_full_body(robot, spec)
        assert len(links) >= 3  # at least pelvis, torso, head
        for link in robot.findall("link"):
            mass_el = link.find("inertial/mass")
            assert float(mass_el.get("value")) > 0

    def test_very_large_person(self) -> None:
        """A very large person should still produce valid URDF."""
        spec = BodyModelSpec(total_mass=200.0, height=2.20)
        robot = ET.Element("robot", name="test")
        links = create_full_body(robot, spec)
        assert len(links) >= 3
        for link in robot.findall("link"):
            mass_el = link.find("inertial/mass")
            assert float(mass_el.get("value")) > 0

    def test_minimum_viable_mass(self) -> None:
        """Smallest reasonable mass should work."""
        spec = BodyModelSpec(total_mass=0.01, height=0.01)
        robot = ET.Element("robot", name="test")
        links = create_full_body(robot, spec)
        assert "pelvis" in links

    def test_mass_partitioning_sums_correctly(self) -> None:
        """All segment masses should sum to approximately total_mass."""
        spec = BodyModelSpec(total_mass=80.0, height=1.75)
        robot = ET.Element("robot", name="test")
        create_full_body(robot, spec)

        total = sum(
            float(link.find("inertial/mass").get("value"))
            for link in robot.findall("link")
        )
        # Sum of mass fractions: pelvis(0.142) + torso(0.355) + head(0.081)
        # + 2*(upper_arm(0.028) + forearm(0.016) + hand(0.006)
        # + thigh(0.100) + shank(0.047) + foot(0.014))
        # = 0.578 + 2*0.211 = 1.000
        assert total == pytest.approx(80.0, rel=0.01)

    def test_bilateral_symmetry(self) -> None:
        """Left and right limbs should have identical masses."""
        spec = BodyModelSpec(total_mass=80.0, height=1.75)
        robot = ET.Element("robot", name="test")
        create_full_body(robot, spec)

        link_masses = {}
        for link in robot.findall("link"):
            name = link.get("name")
            mass = float(link.find("inertial/mass").get("value"))
            link_masses[name] = mass

        for segment in ("upper_arm", "forearm", "hand", "thigh", "shank", "foot"):
            left_mass = link_masses[f"{segment}_l"]
            right_mass = link_masses[f"{segment}_r"]
            assert left_mass == pytest.approx(right_mass), (
                f"{segment} L/R mass mismatch: {left_mass} vs {right_mass}"
            )

    def test_rejects_zero_mass(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            BodyModelSpec(total_mass=0.0, height=1.75)

    def test_rejects_negative_height(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            BodyModelSpec(total_mass=80.0, height=-1.0)

    def test_all_joints_have_limits(self) -> None:
        """Every revolute joint should have proper limits."""
        spec = BodyModelSpec()
        robot = ET.Element("robot", name="test")
        create_full_body(robot, spec)

        for joint in robot.findall("joint[@type='revolute']"):
            limit = joint.find("limit")
            assert limit is not None, f"Joint {joint.get('name')} missing limits"
            lower = float(limit.get("lower"))
            upper = float(limit.get("upper"))
            assert lower < upper, (
                f"Joint {joint.get('name')}: lower ({lower}) >= upper ({upper})"
            )

    def test_all_inertias_satisfy_triangle_inequality(self) -> None:
        """All body inertias should satisfy the triangle inequality."""
        spec = BodyModelSpec(total_mass=80.0, height=1.75)
        robot = ET.Element("robot", name="test")
        create_full_body(robot, spec)

        for link in robot.findall("link"):
            inertia_el = link.find("inertial/inertia")
            ixx = float(inertia_el.get("ixx"))
            iyy = float(inertia_el.get("iyy"))
            izz = float(inertia_el.get("izz"))
            name = link.get("name")
            assert ixx + iyy >= izz, f"{name} triangle inequality failed"
            assert ixx + izz >= iyy, f"{name} triangle inequality failed"
            assert iyy + izz >= ixx, f"{name} triangle inequality failed"
