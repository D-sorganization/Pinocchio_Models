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
)


class TestRequirePositive:
    def test_accepts_positive(self):
        require_positive(1.0, "x")

    def test_rejects_zero(self):
        with pytest.raises(ValueError, match="must be positive"):
            require_positive(0.0, "x")

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="must be positive"):
            require_positive(-1.0, "x")


class TestRequireNonNegative:
    def test_accepts_zero(self):
        require_non_negative(0.0, "x")

    def test_accepts_positive(self):
        require_non_negative(5.0, "x")

    def test_rejects_negative(self):
        with pytest.raises(ValueError, match="must be non-negative"):
            require_non_negative(-0.1, "x")


class TestRequireUnitVector:
    def test_accepts_unit_vector(self):
        require_unit_vector([0, 0, 1], "v")

    def test_rejects_non_unit(self):
        with pytest.raises(ValueError, match="unit-length"):
            require_unit_vector([1, 1, 0], "v")

    def test_rejects_wrong_shape(self):
        with pytest.raises(ValueError, match="3-vector"):
            require_unit_vector([1, 0], "v")


class TestRequireFinite:
    def test_accepts_finite(self):
        require_finite([1.0, 2.0, 3.0], "arr")

    def test_rejects_nan(self):
        with pytest.raises(ValueError, match="non-finite"):
            require_finite([1.0, float("nan")], "arr")

    def test_rejects_inf(self):
        with pytest.raises(ValueError, match="non-finite"):
            require_finite([float("inf")], "arr")


class TestRequireInRange:
    def test_accepts_in_range(self):
        require_in_range(5.0, 0.0, 10.0, "x")

    def test_accepts_boundary(self):
        require_in_range(0.0, 0.0, 10.0, "x")
        require_in_range(10.0, 0.0, 10.0, "x")

    def test_rejects_below(self):
        with pytest.raises(ValueError, match="must be in"):
            require_in_range(-1.0, 0.0, 10.0, "x")

    def test_rejects_above(self):
        with pytest.raises(ValueError, match="must be in"):
            require_in_range(11.0, 0.0, 10.0, "x")


class TestRequireShape:
    def test_accepts_correct_shape(self):
        require_shape(np.zeros((3, 3)), (3, 3), "m")

    def test_rejects_wrong_shape(self):
        with pytest.raises(ValueError, match="must have shape"):
            require_shape(np.zeros((2, 3)), (3, 3), "m")
