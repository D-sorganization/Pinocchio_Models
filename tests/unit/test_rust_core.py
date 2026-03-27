"""Tests for the Rust accelerator module (pinocchio_models_core).

These tests verify the Python-accessible Rust functions for batch
inverse dynamics, center-of-mass, and phase interpolation. The Rust
extension is optional; tests are skipped if it is not compiled.
"""

import numpy as np
import pytest

try:
    import pinocchio_models_core  # type: ignore[import-untyped]

    _HAS_RUST = True
except ImportError:
    _HAS_RUST = False

pytestmark = pytest.mark.skipif(not _HAS_RUST, reason="Rust extension not compiled")


class TestInverseDynamicsBatch:
    def test_zero_motion_gravity_only(self) -> None:
        """With zero velocity and acceleration, torque = m * g * cos(q)."""
        batch, nq = 2, 3
        q = np.zeros((batch, nq))
        qd = np.zeros((batch, nq))
        qdd = np.zeros((batch, nq))
        masses = np.array([1.0, 2.0, 3.0])
        gravity = 9.81

        tau = pinocchio_models_core.inverse_dynamics_batch(q, qd, qdd, masses, gravity)

        assert tau.shape == (batch, nq)
        for i in range(batch):
            for j in range(nq):
                expected = masses[j] * gravity  # cos(0) = 1
                assert tau[i, j] == pytest.approx(expected, abs=1e-10)

    def test_output_shape(self) -> None:
        batch, nq = 5, 4
        q = np.random.randn(batch, nq)
        qd = np.random.randn(batch, nq)
        qdd = np.random.randn(batch, nq)
        masses = np.ones(nq)
        tau = pinocchio_models_core.inverse_dynamics_batch(q, qd, qdd, masses, 9.81)
        assert tau.shape == (batch, nq)


class TestComBatch:
    def test_zero_angles(self) -> None:
        """At q=0: sin(0)=0 so COM x=0, cos(0)=1 so COM y=1."""
        batch, nq = 1, 4
        q = np.zeros((batch, nq))
        masses = np.ones(nq)
        com = pinocchio_models_core.com_batch(q, masses)
        assert com.shape == (batch, 3)
        assert com[0, 0] == pytest.approx(0.0, abs=1e-10)
        assert com[0, 1] == pytest.approx(1.0, abs=1e-10)

    def test_output_shape(self) -> None:
        batch, nq = 3, 5
        q = np.random.randn(batch, nq)
        masses = np.ones(nq)
        com = pinocchio_models_core.com_batch(q, masses)
        assert com.shape == (batch, 3)


class TestInterpolatePhases:
    def test_linear_two_phases(self) -> None:
        """Two phase boundaries at 0 and 1 — linear interpolation."""
        fracs = np.array([0.0, 1.0])
        angles = np.array([[0.0, 0.0], [1.0, 2.0]])
        n_frames = 3

        result = pinocchio_models_core.interpolate_phases_rs(fracs, angles, n_frames)

        assert result.shape == (3, 2)
        np.testing.assert_allclose(result[0], [0.0, 0.0], atol=1e-10)
        np.testing.assert_allclose(result[1], [0.5, 1.0], atol=1e-10)
        np.testing.assert_allclose(result[2], [1.0, 2.0], atol=1e-10)

    def test_single_frame(self) -> None:
        """n_frames=1 returns the first phase angles."""
        fracs = np.array([0.0, 1.0])
        angles = np.array([[5.0], [10.0]])
        result = pinocchio_models_core.interpolate_phases_rs(fracs, angles, 1)
        assert result.shape == (1, 1)
        assert result[0, 0] == pytest.approx(5.0, abs=1e-10)
