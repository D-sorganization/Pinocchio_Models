"""Tests for postcondition contract guards."""

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exceptions import URDFError
from pinocchio_models.shared.contracts.postconditions import (
    _collect_link_names,
    _parse_robot_root,
    _validate_joint_links,
    ensure_positive_definite_inertia,
    ensure_positive_mass,
    ensure_valid_urdf,
)


class TestEnsureValidUrdf:
    def test_accepts_valid_urdf(self) -> None:
        root = ensure_valid_urdf('<robot name="test"/>')
        assert root.tag == "robot"

    def test_rejects_malformed_xml(self) -> None:
        with pytest.raises(URDFError, match="not well-formed") as exc_info:
            ensure_valid_urdf("<robot><unclosed>")
        assert exc_info.value.error_code == "PM204"

    def test_rejects_non_robot_root(self) -> None:
        with pytest.raises(URDFError, match="root must be <robot>") as exc_info:
            ensure_valid_urdf("<model/>")
        assert exc_info.value.error_code == "PM203"


class TestParseRobotRoot:
    def test_returns_root_for_valid_xml(self) -> None:
        root = _parse_robot_root('<robot name="r"/>')
        assert root.tag == "robot"

    def test_rejects_non_robot_tag(self) -> None:
        with pytest.raises(URDFError, match="root must be <robot>") as exc_info:
            _parse_robot_root("<thing/>")
        assert exc_info.value.error_code == "PM203"


class TestCollectLinkNames:
    def test_collects_named_links(self) -> None:
        root = ET.fromstring('<robot><link name="a"/><link name="b"/><link/></robot>')
        assert _collect_link_names(root) == {"a", "b"}


class TestValidateJointLinks:
    def test_rejects_unknown_child_link(self) -> None:
        root = ET.fromstring(
            '<robot><link name="a"/>'
            '<joint name="j"><parent link="a"/><child link="ghost"/></joint>'
            "</robot>"
        )
        with pytest.raises(ValueError, match="unknown child link"):
            _validate_joint_links(root, {"a"})

    def test_rejects_duplicate_child_link(self) -> None:
        root = ET.fromstring(
            '<robot><link name="a"/><link name="b"/>'
            '<joint name="j1"><parent link="a"/><child link="b"/></joint>'
            '<joint name="j2"><parent link="a"/><child link="b"/></joint>'
            "</robot>"
        )
        with pytest.raises(ValueError, match="exactly one parent joint"):
            _validate_joint_links(root, {"a", "b"})


class TestEnsurePositiveMass:
    def test_accepts_positive(self) -> None:
        ensure_positive_mass(1.0, "body")

    def test_rejects_zero(self) -> None:
        with pytest.raises(ValueError, match="not positive"):
            ensure_positive_mass(0.0, "body")

    def test_rejects_negative(self) -> None:
        with pytest.raises(ValueError, match="not positive"):
            ensure_positive_mass(-1.0, "body")


class TestEnsurePositiveDefiniteInertia:
    def test_accepts_valid_inertia(self) -> None:
        ensure_positive_definite_inertia(1.0, 1.0, 1.0, "body")

    def test_rejects_zero_component(self) -> None:
        with pytest.raises(ValueError, match="not positive"):
            ensure_positive_definite_inertia(0.0, 1.0, 1.0, "body")

    def test_rejects_triangle_inequality_violation(self) -> None:
        with pytest.raises(ValueError, match="triangle inequality"):
            ensure_positive_definite_inertia(0.1, 0.1, 10.0, "body")
