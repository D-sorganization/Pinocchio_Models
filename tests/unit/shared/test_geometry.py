"""Tests for geometry and inertia utilities."""

import math

import numpy as np
import pytest

from pinocchio_models.shared.utils.geometry import (
    cylinder_inertia,
    parallel_axis_shift,
    rectangular_prism_inertia,
    rotation_matrix_x,
    rotation_matrix_y,
    rotation_matrix_z,
    sphere_inertia,
)


class TestCylinderInertia:
    def test_known_values(self):
        mass, radius, length = 10.0, 0.1, 1.0
        ixx, iyy, izz = cylinder_inertia(mass, radius, length)
        # Axial: Izz = 0.5 * m * r^2
        assert izz == pytest.approx(0.5 * mass * radius**2)
        # Transverse: Ixx = (1/12) * m * (3r^2 + L^2)
        expected_trans = (1.0 / 12.0) * mass * (3 * radius**2 + length**2)
        assert ixx == pytest.approx(expected_trans)
        assert iyy == pytest.approx(expected_trans)

    def test_rejects_zero_mass(self):
        with pytest.raises(ValueError, match="must be positive"):
            cylinder_inertia(0.0, 0.1, 1.0)

    def test_rejects_negative_radius(self):
        with pytest.raises(ValueError, match="must be positive"):
            cylinder_inertia(1.0, -0.1, 1.0)


class TestRectangularPrismInertia:
    def test_cube_symmetry(self):
        ixx, iyy, izz = rectangular_prism_inertia(12.0, 1.0, 1.0, 1.0)
        assert ixx == pytest.approx(iyy)
        assert iyy == pytest.approx(izz)

    def test_rejects_zero_dimension(self):
        with pytest.raises(ValueError, match="must be positive"):
            rectangular_prism_inertia(1.0, 0.0, 1.0, 1.0)


class TestSphereInertia:
    def test_known_value(self):
        mass, radius = 5.0, 0.2
        ixx, iyy, izz = sphere_inertia(mass, radius)
        expected = (2.0 / 5.0) * mass * radius**2
        assert ixx == pytest.approx(expected)
        assert iyy == pytest.approx(expected)
        assert izz == pytest.approx(expected)


class TestParallelAxisShift:
    def test_zero_displacement(self):
        inertia = (1.0, 2.0, 3.0)
        result = parallel_axis_shift(5.0, inertia, np.zeros(3))
        assert result[0] == pytest.approx(1.0)
        assert result[1] == pytest.approx(2.0)
        assert result[2] == pytest.approx(3.0)

    def test_nonzero_displacement(self):
        inertia = (1.0, 1.0, 1.0)
        disp = np.array([1.0, 0.0, 0.0])
        mass = 2.0
        ixx, iyy, izz = parallel_axis_shift(mass, inertia, disp)
        # Ixx: displacement is along x, so d_sq - dx*dx = 0
        assert ixx == pytest.approx(1.0)
        # Iyy: d_sq - dy*dy = 1.0, so +2.0
        assert iyy == pytest.approx(3.0)
        # Izz: same as Iyy
        assert izz == pytest.approx(3.0)


class TestRotationMatrices:
    def test_identity_at_zero(self):
        for func in [rotation_matrix_x, rotation_matrix_y, rotation_matrix_z]:
            r = func(0.0)
            np.testing.assert_allclose(r, np.eye(3), atol=1e-12)

    def test_orthogonal(self):
        angle = math.pi / 4
        for func in [rotation_matrix_x, rotation_matrix_y, rotation_matrix_z]:
            r = func(angle)
            np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-12)

    def test_determinant_one(self):
        angle = 1.23
        for func in [rotation_matrix_x, rotation_matrix_y, rotation_matrix_z]:
            r = func(angle)
            assert np.linalg.det(r) == pytest.approx(1.0)
