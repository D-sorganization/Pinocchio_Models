"""Tests for URDF XML generation helpers."""

import xml.etree.ElementTree as ET

from pinocchio_models.shared.utils.urdf_helpers import (
    add_continuous_joint,
    add_fixed_joint,
    add_link,
    add_revolute_joint,
    make_box_geometry,
    make_cylinder_geometry,
    make_sphere_geometry,
    serialize_model,
    vec3_str,
)


class TestVec3Str:
    def test_formats_correctly(self):
        assert vec3_str(1.0, 2.5, -3.0) == "1.000000 2.500000 -3.000000"

    def test_zero(self):
        assert vec3_str(0, 0, 0) == "0.000000 0.000000 0.000000"


class TestAddLink:
    def test_creates_link_with_inertial(self):
        robot = ET.Element("robot", name="test")
        link = add_link(robot, name="body1", mass=5.0, ixx=0.1, iyy=0.2, izz=0.3)
        assert link.get("name") == "body1"
        inertial = link.find("inertial")
        assert inertial is not None
        assert inertial.find("mass").get("value") == "5.000000"

    def test_creates_link_with_visual(self):
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
        assert visual.find("geometry/cylinder") is not None


class TestAddRevoluteJoint:
    def test_creates_joint(self):
        robot = ET.Element("robot", name="test")
        joint = add_revolute_joint(
            robot,
            name="j1",
            parent="p",
            child="c",
            origin_xyz=(0, 0, 1),
            axis=(0, 1, 0),
        )
        assert joint.get("type") == "revolute"
        assert joint.find("parent").get("link") == "p"
        assert joint.find("child").get("link") == "c"
        assert joint.find("axis") is not None
        assert joint.find("limit") is not None


class TestAddFixedJoint:
    def test_creates_fixed_joint(self):
        robot = ET.Element("robot", name="test")
        joint = add_fixed_joint(robot, name="w1", parent="p", child="c")
        assert joint.get("type") == "fixed"
        assert joint.find("parent").get("link") == "p"
        assert joint.find("child").get("link") == "c"


class TestAddContinuousJoint:
    def test_creates_continuous_joint(self):
        robot = ET.Element("robot", name="test")
        joint = add_continuous_joint(
            robot,
            name="cj1",
            parent="p",
            child="c",
        )
        assert joint.get("type") == "continuous"


class TestGeometryFactories:
    def test_cylinder(self):
        geom = make_cylinder_geometry(0.05, 1.0)
        cyl = geom.find("cylinder")
        assert cyl is not None
        assert cyl.get("radius") == "0.050000"
        assert cyl.get("length") == "1.000000"

    def test_box(self):
        geom = make_box_geometry(1.0, 2.0, 3.0)
        box = geom.find("box")
        assert box is not None

    def test_sphere(self):
        geom = make_sphere_geometry(0.1)
        sph = geom.find("sphere")
        assert sph is not None
        assert sph.get("radius") == "0.100000"


class TestSerializeModel:
    def test_produces_xml_declaration(self):
        root = ET.Element("robot", name="test")
        ET.SubElement(root, "link", name="base")
        xml_str = serialize_model(root)
        assert "<?xml" in xml_str
        assert "<robot" in xml_str
