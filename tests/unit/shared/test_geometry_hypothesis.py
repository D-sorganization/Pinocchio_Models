"""Property-based tests for geometry functions using Hypothesis."""

from __future__ import annotations

import numpy as np
import pytest

pytest.importorskip("hypothesis")

from hypothesis import given, settings
from hypothesis import strategies as st

from pinocchio_models.shared.utils.geometry import (
    cylinder_inertia,
    parallel_axis_shift,
    rectangular_prism_inertia,
    rotation_matrix_x,
    rotation_matrix_y,
    rotation_matrix_z,
    sphere_inertia,
)

# Strategy for positive floats suitable for physics parameters
positive_float = st.floats(
    min_value=0.01, max_value=1e4, allow_nan=False, allow_infinity=False
)
small_float = st.floats(
    min_value=-10.0, max_value=10.0, allow_nan=False, allow_infinity=False
)
angle = st.floats(
    min_value=-2 * np.pi, max_value=2 * np.pi, allow_nan=False, allow_infinity=False
)


class TestCylinderInertiaProperties:
    @given(mass=positive_float, radius=positive_float, length=positive_float)
    @settings(max_examples=50)
    def test_all_inertias_positive(
        self, mass: float, radius: float, length: float
    ) -> None:
        ixx, iyy, izz = cylinder_inertia(mass, radius, length)
        assert ixx > 0
        assert iyy > 0
        assert izz > 0

    @given(mass=positive_float, radius=positive_float, length=positive_float)
    @settings(max_examples=50)
    def test_transverse_symmetry(
        self, mass: float, radius: float, length: float
    ) -> None:
        ixx, iyy, _izz = cylinder_inertia(mass, radius, length)
        assert abs(ixx - iyy) < 1e-10 * max(abs(ixx), 1.0)

    @given(mass=positive_float, radius=positive_float, length=positive_float)
    @settings(max_examples=50)
    def test_triangle_inequality(
        self, mass: float, radius: float, length: float
    ) -> None:
        ixx, iyy, izz = cylinder_inertia(mass, radius, length)
        assert ixx + iyy >= izz
        assert ixx + izz >= iyy
        assert iyy + izz >= ixx

    @given(mass=positive_float, radius=positive_float, length=positive_float)
    @settings(max_examples=50)
    def test_scales_linearly_with_mass(
        self, mass: float, radius: float, length: float
    ) -> None:
        ixx1, iyy1, izz1 = cylinder_inertia(mass, radius, length)
        ixx2, iyy2, izz2 = cylinder_inertia(2 * mass, radius, length)
        assert abs(ixx2 - 2 * ixx1) < 1e-10 * max(abs(ixx2), 1.0)
        assert abs(iyy2 - 2 * iyy1) < 1e-10 * max(abs(iyy2), 1.0)
        assert abs(izz2 - 2 * izz1) < 1e-10 * max(abs(izz2), 1.0)


class TestRectangularPrismInertiaProperties:
    @given(
        mass=positive_float,
        width=positive_float,
        height=positive_float,
        depth=positive_float,
    )
    @settings(max_examples=50)
    def test_all_positive(
        self, mass: float, width: float, height: float, depth: float
    ) -> None:
        ixx, iyy, izz = rectangular_prism_inertia(mass, width, height, depth)
        assert ixx > 0
        assert iyy > 0
        assert izz > 0

    @given(mass=positive_float, side=positive_float)
    @settings(max_examples=50)
    def test_cube_all_equal(self, mass: float, side: float) -> None:
        ixx, iyy, izz = rectangular_prism_inertia(mass, side, side, side)
        assert abs(ixx - iyy) < 1e-10 * max(abs(ixx), 1.0)
        assert abs(iyy - izz) < 1e-10 * max(abs(iyy), 1.0)


class TestSphereInertiaProperties:
    @given(mass=positive_float, radius=positive_float)
    @settings(max_examples=50)
    def test_all_equal(self, mass: float, radius: float) -> None:
        ixx, iyy, izz = sphere_inertia(mass, radius)
        assert abs(ixx - iyy) < 1e-10 * max(abs(ixx), 1.0)
        assert abs(iyy - izz) < 1e-10 * max(abs(iyy), 1.0)

    @given(mass=positive_float, radius=positive_float)
    @settings(max_examples=50)
    def test_positive(self, mass: float, radius: float) -> None:
        ixx, iyy, izz = sphere_inertia(mass, radius)
        assert ixx > 0


class TestParallelAxisShiftProperties:
    @given(mass=positive_float)
    @settings(max_examples=50)
    def test_zero_displacement_identity(self, mass: float) -> None:
        inertia = (1.0, 2.0, 3.0)
        result = parallel_axis_shift(mass, inertia, np.zeros(3))
        assert abs(result[0] - 1.0) < 1e-10
        assert abs(result[1] - 2.0) < 1e-10
        assert abs(result[2] - 3.0) < 1e-10

    @given(
        mass=positive_float,
        dx=small_float,
        dy=small_float,
        dz=small_float,
    )
    @settings(max_examples=50)
    def test_inertia_never_decreases(
        self, mass: float, dx: float, dy: float, dz: float
    ) -> None:
        inertia = (1.0, 1.0, 1.0)
        result = parallel_axis_shift(mass, inertia, np.array([dx, dy, dz]))
        assert result[0] >= inertia[0] - 1e-10
        assert result[1] >= inertia[1] - 1e-10
        assert result[2] >= inertia[2] - 1e-10


class TestRotationMatrixProperties:
    @given(theta=angle)
    @settings(max_examples=50)
    def test_orthogonality_x(self, theta: float) -> None:
        r = rotation_matrix_x(theta)
        np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-12)

    @given(theta=angle)
    @settings(max_examples=50)
    def test_orthogonality_y(self, theta: float) -> None:
        r = rotation_matrix_y(theta)
        np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-12)

    @given(theta=angle)
    @settings(max_examples=50)
    def test_orthogonality_z(self, theta: float) -> None:
        r = rotation_matrix_z(theta)
        np.testing.assert_allclose(r @ r.T, np.eye(3), atol=1e-12)

    @given(theta=angle)
    @settings(max_examples=50)
    def test_determinant_one(self, theta: float) -> None:
        for func in [rotation_matrix_x, rotation_matrix_y, rotation_matrix_z]:
            r = func(theta)
            assert abs(np.linalg.det(r) - 1.0) < 1e-10
