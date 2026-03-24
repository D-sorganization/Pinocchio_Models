"""Tests for postcondition contract guards."""

import pytest

from pinocchio_models.shared.contracts.postconditions import (
    ensure_positive_definite_inertia,
    ensure_positive_mass,
    ensure_valid_urdf,
)


class TestEnsureValidUrdf:
    def test_accepts_valid_urdf(self) -> None:
        root = ensure_valid_urdf('<robot name="test"/>')
        assert root.tag == "robot"

    def test_rejects_malformed_xml(self) -> None:
        with pytest.raises(ValueError, match="not well-formed"):
            ensure_valid_urdf("<robot><unclosed>")

    def test_rejects_non_robot_root(self) -> None:
        with pytest.raises(ValueError, match="root must be <robot>"):
            ensure_valid_urdf("<model/>")


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
