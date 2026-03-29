"""Tests for precondition contract guards."""

import numpy as np
import pytest

from pinocchio_models.shared.contracts.preconditions import (
    require_finite,
    require_in_range,
    require_non_negative,
    require_positive,
    require_shape,
    require_unit_vector,
    require_valid_exercise_name,
    require_valid_urdf_string,
)


class TestRequirePositive:
    def test_accepts_positive(self) -> None:
        require_positive(1.0, "x")

    def test_rejects_zero(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            require_positive(0.0, "x")

    def test_rejects_negative(self) -> None:
        with pytest.raises(ValueError, match="must be positive"):
            require_positive(-1.0, "x")


class TestRequireNonNegative:
    def test_accepts_zero(self) -> None:
        require_non_negative(0.0, "x")

    def test_accepts_positive(self) -> None:
        require_non_negative(5.0, "x")

    def test_rejects_negative(self) -> None:
        with pytest.raises(ValueError, match="must be non-negative"):
            require_non_negative(-0.1, "x")


class TestRequireUnitVector:
    def test_accepts_unit_vector(self) -> None:
        require_unit_vector([0, 0, 1], "v")

    def test_rejects_non_unit(self) -> None:
        with pytest.raises(ValueError, match="unit-length"):
            require_unit_vector([1, 1, 0], "v")

    def test_rejects_wrong_shape(self) -> None:
        with pytest.raises(ValueError, match="3-vector"):
            require_unit_vector([1, 0], "v")


class TestRequireFinite:
    def test_accepts_finite(self) -> None:
        require_finite([1.0, 2.0, 3.0], "arr")

    def test_rejects_nan(self) -> None:
        with pytest.raises(ValueError, match="non-finite"):
            require_finite([1.0, float("nan")], "arr")

    def test_rejects_inf(self) -> None:
        with pytest.raises(ValueError, match="non-finite"):
            require_finite([float("inf")], "arr")


class TestRequireInRange:
    def test_accepts_in_range(self) -> None:
        require_in_range(5.0, 0.0, 10.0, "x")

    def test_accepts_boundary(self) -> None:
        require_in_range(0.0, 0.0, 10.0, "x")
        require_in_range(10.0, 0.0, 10.0, "x")

    def test_rejects_below(self) -> None:
        with pytest.raises(ValueError, match="must be in"):
            require_in_range(-1.0, 0.0, 10.0, "x")

    def test_rejects_above(self) -> None:
        with pytest.raises(ValueError, match="must be in"):
            require_in_range(11.0, 0.0, 10.0, "x")


class TestRequireShape:
    def test_accepts_correct_shape(self) -> None:
        require_shape(np.zeros((3, 3)), (3, 3), "m")

    def test_rejects_wrong_shape(self) -> None:
        with pytest.raises(ValueError, match="must have shape"):
            require_shape(np.zeros((2, 3)), (3, 3), "m")


class TestRequireValidExerciseName:
    def test_accepts_valid_names(self) -> None:
        for name in ("back_squat", "deadlift", "gait", "sit_to_stand"):
            require_valid_exercise_name(name)

    def test_rejects_unknown_name(self) -> None:
        with pytest.raises(ValueError, match="Unknown exercise"):
            require_valid_exercise_name("jumping_jacks")

    def test_error_lists_valid_options(self) -> None:
        with pytest.raises(ValueError, match="back_squat"):
            require_valid_exercise_name("invalid")


class TestRequireValidUrdfString:
    """Tests for URDF string validation (issue #55)."""

    def test_accepts_valid_urdf(self) -> None:
        urdf = '<?xml version="1.0" ?><robot name="test"></robot>'
        require_valid_urdf_string(urdf)

    def test_accepts_minimal_robot(self) -> None:
        require_valid_urdf_string('<robot name="r"/>')

    def test_rejects_empty_string(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            require_valid_urdf_string("")

    def test_rejects_whitespace_only(self) -> None:
        with pytest.raises(ValueError, match="must not be empty"):
            require_valid_urdf_string("   \n  ")

    def test_rejects_malformed_xml(self) -> None:
        with pytest.raises(ValueError, match="not valid XML"):
            require_valid_urdf_string("<robot><broken")

    def test_rejects_non_robot_root(self) -> None:
        with pytest.raises(ValueError, match="must be <robot>"):
            require_valid_urdf_string("<model/>")

    def test_rejects_html(self) -> None:
        with pytest.raises(ValueError, match="must be <robot>"):
            require_valid_urdf_string("<html><body>hi</body></html>")
