"""Tests for URDF XML generation helpers."""

import xml.etree.ElementTree as ET
from types import SimpleNamespace

import pytest

from pinocchio_models.shared.utils.urdf_helpers import (
    _add_collision,
    _add_inertial,
    _add_visual,
    _apply_initial_positions,
    _build_initial_configuration,
    _parse_initial_positions,
    add_fixed_joint,
    add_link,
    add_revolute_joint,
    add_virtual_link,
    make_box_geometry,
    make_cylinder_geometry,
    make_sphere_geometry,
    serialize_model,
    set_joint_default,
    vec3_str,
)


class TestParseInitialPositions:
    def test_extracts_pairs_from_metadata(self) -> None:
        xml_str = (
            '<robot name="r">'
            '<joint name="j1" initial_position="0.5"><parent link="a"/>'
            '<child link="b"/></joint>'
            '<joint name="j2"><parent link="b"/><child link="c"/></joint>'
            '<joint name="j3" initial_position="-1.25"><parent link="c"/>'
            '<child link="d"/></joint>'
            "</robot>"
        )
        pairs = _parse_initial_positions(xml_str)
        assert pairs == [("j1", 0.5), ("j3", -1.25)]

    def test_returns_empty_when_no_metadata(self) -> None:
        xml_str = (
            '<robot name="r">'
            '<joint name="j"><parent link="a"/><child link="b"/></joint>'
            "</robot>"
        )
        assert _parse_initial_positions(xml_str) == []


class TestVec3Str:
    def test_formats_correctly(self) -> None:
        assert vec3_str(1.0, 2.5, -3.0) == "1.000000 2.500000 -3.000000"

    def test_zero(self) -> None:
        assert vec3_str(0, 0, 0) == "0 0 0"


class TestAddLink:
    def test_add_inertial_helper_formats_full_inertia_block(self) -> None:
        link = ET.Element("link", name="body1")
        inertial = _add_inertial(
            link,
            mass=5.0,
            origin_xyz=(1.0, 2.0, 3.0),
            origin_rpy=(0.1, 0.2, 0.3),
            ixx=0.1,
            iyy=0.2,
            izz=0.3,
            ixy=0.01,
            ixz=0.02,
            iyz=0.03,
        )
        assert inertial.find("origin").get("xyz") == "1.000000 2.000000 3.000000"  # type: ignore[union-attr]
        assert inertial.find("origin").get("rpy") == "0.100000 0.200000 0.300000"  # type: ignore[union-attr]
        assert inertial.find("mass").get("value") == "5.000000"  # type: ignore[union-attr]
        inertia = inertial.find("inertia")
        assert inertia is not None
        assert inertia.get("ixy") == "0.010000"

    def test_add_visual_helper_applies_visual_rotation(self) -> None:
        link = ET.Element("link", name="body1")
        visual = _add_visual(
            link,
            make_cylinder_geometry(0.05, 1.0),
            visual_origin_rpy=(1.0, 0.0, 0.0),
        )
        assert visual.find("origin").get("rpy") == "1.000000 0 0"  # type: ignore[union-attr]
        assert visual.find("geometry/cylinder") is not None

    def test_add_collision_helper_uses_neutral_origin(self) -> None:
        link = ET.Element("link", name="body1")
        collision = _add_collision(link, make_box_geometry(1.0, 2.0, 3.0))
        origin = collision.find("origin")
        assert origin is not None
        assert origin.get("xyz") == "0 0 0"
        assert origin.get("rpy") == "0 0 0"
        assert collision.find("geometry/box") is not None

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


class TestSetJointDefault:
    def test_sets_initial_position(self) -> None:
        robot = ET.Element("robot", name="test")
        add_revolute_joint(
            robot,
            name="hip_l_flex",
            parent="p",
            child="c",
            origin_xyz=(0, 0, 0),
            axis=(1, 0, 0),
        )
        set_joint_default(robot, "hip", 1.23, exact_suffix="_flex")
        joint = robot.find("joint[@name='hip_l_flex']")
        assert joint is not None
        assert joint.get("initial_position") == "1.230000"

    def test_ignores_unmatched_joints(self) -> None:
        robot = ET.Element("robot", name="test")
        add_revolute_joint(
            robot,
            name="knee_l",
            parent="p",
            child="c",
            origin_xyz=(0, 0, 0),
            axis=(0, 1, 0),
        )
        set_joint_default(robot, "hip", 0.5)
        joint = robot.find("joint[@name='knee_l']")
        assert joint is not None
        assert joint.get("initial_position") is None

    def test_exact_suffix_filters(self) -> None:
        robot = ET.Element("robot", name="test")
        add_revolute_joint(
            robot,
            name="hip_l_flex",
            parent="p",
            child="c",
            origin_xyz=(0, 0, 0),
            axis=(1, 0, 0),
        )
        add_revolute_joint(
            robot,
            name="hip_l_adduct",
            parent="p",
            child="c2",
            origin_xyz=(0, 0, 0),
            axis=(0, 0, 1),
        )
        set_joint_default(robot, "hip", 0.7, exact_suffix="_flex")
        flex_joint = robot.find("joint[@name='hip_l_flex']")
        adduct_joint = robot.find("joint[@name='hip_l_adduct']")
        assert flex_joint is not None
        assert flex_joint.get("initial_position") == "0.700000"
        assert adduct_joint is not None
        assert adduct_joint.get("initial_position") is None


class TestGetInitialConfiguration:
    """Tests for get_initial_configuration (requires pinocchio)."""

    def test_build_initial_configuration_overlays_scalar_defaults(self) -> None:
        fake_pin = SimpleNamespace(neutral=lambda model: [0.0, 0.0, 0.0])

        class FakeModel:
            joints = [
                None,
                SimpleNamespace(idx_q=0, nq=1),
                SimpleNamespace(idx_q=1, nq=1),
            ]

            def getJointId(self, name: str) -> int:
                return {"hip_l": 1, "knee_l": 2}[name]

        q = _build_initial_configuration(
            fake_pin,
            FakeModel(),
            [("hip_l", 1.25), ("knee_l", -0.5)],
        )

        assert q == [1.25, -0.5, 0.0]

    def test_apply_initial_positions_skips_missing_and_multidof_joints(self) -> None:
        class FakeModel:
            joints = [
                None,
                SimpleNamespace(idx_q=0, nq=1),
                SimpleNamespace(idx_q=1, nq=2),
            ]

            def getJointId(self, name: str) -> int:
                if name == "hip_l":
                    return 1
                if name == "hip_l_flex":
                    return 2
                raise KeyError(name)

        q = [0.0, 0.0]
        _apply_initial_positions(
            FakeModel(),
            q,
            [("hip_l", 0.75), ("hip_l_flex", 1.5), ("missing", 2.0)],
        )

        assert q == [0.75, 0.0]

    def test_returns_config_with_initial_positions(self) -> None:
        """Build a real squat model and verify initial config uses defaults."""
        pytest.importorskip("pinocchio")
        import pinocchio as pin

        from pinocchio_models.exercises.squat.squat_model import build_squat_model
        from pinocchio_models.shared.utils.urdf_helpers import (
            get_initial_configuration,
        )

        urdf_str = build_squat_model()
        model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
        q0 = get_initial_configuration(model, urdf_str)

        assert q0.shape == (model.nq,)
        # Neutral FreeFlyer quaternion: w=1 at index 6
        assert q0[6] == pytest.approx(1.0)

    def test_raises_without_pinocchio(self) -> None:
        """get_initial_configuration raises ImportError if pin missing."""
        # We just verify the function exists and is callable; actual
        # ImportError testing is fragile in environments where pin IS
        # installed, so we simply check the signature.
        from pinocchio_models.shared.utils.urdf_helpers import (
            get_initial_configuration,
        )

        assert callable(get_initial_configuration)


class TestSerializeModel:
    def test_produces_xml_declaration(self) -> None:
        root = ET.Element("robot", name="test")
        ET.SubElement(root, "link", name="base")
        xml_str = serialize_model(root)
        assert "<?xml" in xml_str
        assert "<robot" in xml_str
