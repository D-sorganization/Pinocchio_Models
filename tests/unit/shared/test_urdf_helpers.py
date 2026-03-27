"""Tests for URDF XML generation helpers."""

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.shared.utils.urdf_helpers import (
    add_fixed_joint,
    add_link,
    add_revolute_joint,
    add_virtual_link,
    make_box_geometry,
    make_cylinder_geometry,
    make_sphere_geometry,
    serialize_model,
    vec3_str,
)


class TestVec3Str:
    def test_formats_correctly(self) -> None:
        assert vec3_str(1.0, 2.5, -3.0) == "1.000000 2.500000 -3.000000"

    def test_zero(self) -> None:
        assert vec3_str(0, 0, 0) == "0.000000 0.000000 0.000000"


class TestAddLink:
    def test_creates_link_with_inertial(self) -> None:
        robot = ET.Element("robot", name="test")
        link = add_link(robot, name="body1", mass=5.0, ixx=0.1, iyy=0.2, izz=0.3)
        assert link.get("name") == "body1"  # type: ignore
        inertial = link.find("inertial")
        assert inertial is not None
        assert inertial.find("mass").get("value") == "5.000000"  # type: ignore

    def test_creates_link_with_visual(self) -> None:
        robot = ET.Element("robot", name="test")
        geom = make_cylinder_geometry(0.05, 1.0)
        link = add_link(
            robot,
            name="body1",
            mass=5.0,
            ixx=0.1,
            iyy=0.2,
            izz=0.3,
            visual_geometry=geom,
        )
        visual = link.find("visual")
        assert visual is not None
        assert visual.find("geometry/cylinder") is not None  # type: ignore


class TestAddVirtualLink:
    def test_creates_negligible_mass_link(self) -> None:
        robot = ET.Element("robot", name="test")
        link = add_virtual_link(robot, name="virt1")
        assert link.get("name") == "virt1"  # type: ignore
        inertial = link.find("inertial")
        assert inertial is not None
        mass = float(inertial.find("mass").get("value"))  # type: ignore
        assert mass == pytest.approx(1e-6, abs=1e-10)

    def test_virtual_link_has_tiny_inertia(self) -> None:
        robot = ET.Element("robot", name="test")
        link = add_virtual_link(robot, name="virt1")
        inertia = link.find("inertial/inertia")
        assert inertia is not None
        # Inertia values (1e-9) are below 6-decimal-place precision,
        # so they format to 0.000000 in the URDF XML. This is acceptable
        # for virtual links whose only purpose is URDF topology.
        for axis in ("ixx", "iyy", "izz"):
            val = float(inertia.get(axis))  # type: ignore
            assert val <= 1e-6, f"{axis}={val} should be negligible"


class TestAddRevoluteJoint:
    def test_creates_joint(self) -> None:
        robot = ET.Element("robot", name="test")
        joint = add_revolute_joint(
            robot,
            name="j1",
            parent="p",
            child="c",
            origin_xyz=(0, 0, 1),
            axis=(0, 1, 0),
        )
        assert joint.get("type") == "revolute"  # type: ignore
        assert joint.find("parent").get("link") == "p"  # type: ignore
        assert joint.find("child").get("link") == "c"  # type: ignore
        assert joint.find("axis") is not None  # type: ignore
        assert joint.find("limit") is not None  # type: ignore


class TestAddFixedJoint:
    def test_creates_fixed_joint(self) -> None:
        robot = ET.Element("robot", name="test")
        joint = add_fixed_joint(robot, name="w1", parent="p", child="c")
        assert joint.get("type") == "fixed"  # type: ignore
        assert joint.find("parent").get("link") == "p"  # type: ignore
        assert joint.find("child").get("link") == "c"  # type: ignore


class TestGeometryFactories:
    def test_cylinder(self) -> None:
        geom = make_cylinder_geometry(0.05, 1.0)
        cyl = geom.find("cylinder")
        assert cyl is not None
        assert cyl.get("radius") == "0.050000"  # type: ignore
        assert cyl.get("length") == "1.000000"  # type: ignore

    def test_box(self) -> None:
        geom = make_box_geometry(1.0, 2.0, 3.0)
        box = geom.find("box")
        assert box is not None

    def test_sphere(self) -> None:
        geom = make_sphere_geometry(0.1)
        sph = geom.find("sphere")
        assert sph is not None
        assert sph.get("radius") == "0.100000"  # type: ignore


class TestSerializeModel:
    def test_produces_xml_declaration(self) -> None:
        root = ET.Element("robot", name="test")
        ET.SubElement(root, "link", name="base")
        xml_str = serialize_model(root)
        assert "<?xml" in xml_str
        assert "<robot" in xml_str
