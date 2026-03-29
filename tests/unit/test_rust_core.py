"""Tests for the Rust accelerator module (pinocchio_models_core).

These tests verify the Python-accessible Rust functions for batch
inverse dynamics, center-of-mass, and phase interpolation. The Rust
extension is optional; tests are skipped if it is not compiled.

Pure-Python reference implementations are tested unconditionally so
that the Rust logic has validated ground truth even when the extension
is not available (issue #78).
"""

import math

import numpy as np
import pytest

try:
    import pinocchio_models_core  # type: ignore[import-untyped]

    _HAS_RUST = True
except ImportError:
    _HAS_RUST = False


# -------------------------------------------------------------------------
# Pure-Python reference implementations (always testable, issue #78)
# -------------------------------------------------------------------------
def _inverse_dynamics_ref(
    q: np.ndarray,
    qd: np.ndarray,
    qdd: np.ndarray,
    masses: np.ndarray,
    gravity: float,
) -> np.ndarray:
    """Reference inverse dynamics: tau = m*qdd + 0.1*m*qd + m*g*cos(q)."""
    inertia = masses * qdd
    damping = 0.1 * masses * qd
    grav = masses * gravity * np.cos(q)
    return inertia + damping + grav


def _com_ref(q: np.ndarray, masses: np.ndarray) -> np.ndarray:
    """Reference center-of-mass for a single configuration."""
    nq = len(q)
    total_mass = float(np.sum(masses))
    com_x = float(np.sum(masses * np.sin(q))) / total_mass
    com_y = float(np.sum(masses * np.cos(q))) / total_mass
    com_z = float(np.sum(masses * np.arange(nq, dtype=float) / nq)) / total_mass
    return np.array([com_x, com_y, com_z])


def _interpolate_ref(
    fracs: np.ndarray, angles: np.ndarray, n_frames: int
) -> np.ndarray:
    """Reference phase interpolation."""
    n_joints = angles.shape[1]
    result = np.zeros((n_frames, n_joints))
    for i in range(n_frames):
        f = i / max(n_frames - 1, 1)
        prev_idx, next_idx = 0, len(fracs) - 1
        for k in range(len(fracs) - 1):
            if fracs[k] <= f <= fracs[k + 1]:
                prev_idx, next_idx = k, k + 1
                break
        denom = fracs[next_idx] - fracs[prev_idx]
        alpha = 0.0 if abs(denom) < 1e-15 else (f - fracs[prev_idx]) / denom
        result[i] = angles[prev_idx] + alpha * (angles[next_idx] - angles[prev_idx])
    return result


class TestReferenceInverseDynamics:
    """Pure-Python reference tests (always run, issue #78)."""

    def test_zero_motion_gravity_only(self) -> None:
        nq = 3
        q = np.zeros(nq)
        qd = np.zeros(nq)
        qdd = np.zeros(nq)
        masses = np.array([1.0, 2.0, 3.0])
        tau = _inverse_dynamics_ref(q, qd, qdd, masses, 9.81)
        for j in range(nq):
            assert tau[j] == pytest.approx(masses[j] * 9.81, abs=1e-10)

    def test_pure_acceleration(self) -> None:
        nq = 2
        q = np.zeros(nq)
        qd = np.zeros(nq)
        qdd = np.array([1.0, 2.0])
        masses = np.array([3.0, 4.0])
        tau = _inverse_dynamics_ref(q, qd, qdd, masses, 0.0)
        np.testing.assert_allclose(tau, [3.0, 8.0], atol=1e-10)

    def test_damping_contribution(self) -> None:
        nq = 1
        q = np.array([math.pi / 2])  # cos(pi/2) ~ 0
        qd = np.array([10.0])
        qdd = np.zeros(nq)
        masses = np.array([2.0])
        tau = _inverse_dynamics_ref(q, qd, qdd, masses, 0.0)
        assert tau[0] == pytest.approx(0.1 * 2.0 * 10.0, abs=1e-10)

    def test_shape_consistency(self) -> None:
        nq = 5
        tau = _inverse_dynamics_ref(
            np.ones(nq), np.ones(nq), np.ones(nq), np.ones(nq), 9.81
        )
        assert tau.shape == (nq,)


class TestReferenceCom:
    """Pure-Python reference COM tests (always run, issue #78)."""

    def test_zero_angles(self) -> None:
        q = np.zeros(4)
        masses = np.ones(4)
        com = _com_ref(q, masses)
        assert com[0] == pytest.approx(0.0, abs=1e-10)
        assert com[1] == pytest.approx(1.0, abs=1e-10)

    def test_single_joint_pi_over_2(self) -> None:
        q = np.array([math.pi / 2])
        masses = np.array([2.0])
        com = _com_ref(q, masses)
        assert com[0] == pytest.approx(1.0, abs=1e-10)
        assert com[1] == pytest.approx(0.0, abs=1e-10)


class TestReferenceInterpolation:
    """Pure-Python reference interpolation tests (always run, issue #78)."""

    def test_two_phase_linear(self) -> None:
        fracs = np.array([0.0, 1.0])
        angles = np.array([[0.0, 0.0], [1.0, 2.0]])
        result = _interpolate_ref(fracs, angles, 3)
        np.testing.assert_allclose(result[0], [0.0, 0.0], atol=1e-10)
        np.testing.assert_allclose(result[1], [0.5, 1.0], atol=1e-10)
        np.testing.assert_allclose(result[2], [1.0, 2.0], atol=1e-10)

    def test_single_frame(self) -> None:
        fracs = np.array([0.0, 1.0])
        angles = np.array([[5.0], [10.0]])
        result = _interpolate_ref(fracs, angles, 1)
        assert result[0, 0] == pytest.approx(5.0, abs=1e-10)

    def test_three_phases(self) -> None:
        fracs = np.array([0.0, 0.5, 1.0])
        angles = np.array([[0.0], [10.0], [20.0]])
        result = _interpolate_ref(fracs, angles, 5)
        # Frame 0: f=0.0 -> 0.0
        assert result[0, 0] == pytest.approx(0.0, abs=1e-10)
        # Frame 2: f=0.5 -> 10.0
        assert result[2, 0] == pytest.approx(10.0, abs=1e-10)
        # Frame 4: f=1.0 -> 20.0
        assert result[4, 0] == pytest.approx(20.0, abs=1e-10)


# -------------------------------------------------------------------------
# Rust extension tests (skip if not compiled)
# -------------------------------------------------------------------------
pytestmark_rust = pytest.mark.skipif(
    not _HAS_RUST, reason="Rust extension not compiled"
)


@pytest.mark.skipif(not _HAS_RUST, reason="Rust extension not compiled")
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

    def test_matches_reference(self) -> None:
        """Rust batch result must match pure-Python reference."""
        batch, nq = 3, 4
        rng = np.random.default_rng(42)
        q = rng.standard_normal((batch, nq))
        qd = rng.standard_normal((batch, nq))
        qdd = rng.standard_normal((batch, nq))
        masses = np.abs(rng.standard_normal(nq)) + 0.1

        tau = pinocchio_models_core.inverse_dynamics_batch(q, qd, qdd, masses, 9.81)
        for i in range(batch):
            ref = _inverse_dynamics_ref(q[i], qd[i], qdd[i], masses, 9.81)
            np.testing.assert_allclose(tau[i], ref, atol=1e-10)


@pytest.mark.skipif(not _HAS_RUST, reason="Rust extension not compiled")
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

    def test_matches_reference(self) -> None:
        """Rust batch COM must match pure-Python reference."""
        nq = 4
        rng = np.random.default_rng(42)
        q = rng.standard_normal((1, nq))
        masses = np.abs(rng.standard_normal(nq)) + 0.1

        com = pinocchio_models_core.com_batch(q, masses)
        ref = _com_ref(q[0], masses)
        np.testing.assert_allclose(com[0], ref, atol=1e-10)


@pytest.mark.skipif(not _HAS_RUST, reason="Rust extension not compiled")
class TestInterpolatePhases:
    def test_linear_two_phases(self) -> None:
        """Two phase boundaries at 0 and 1 -- linear interpolation."""
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

    def test_matches_reference(self) -> None:
        """Rust interpolation must match pure-Python reference."""
        fracs = np.array([0.0, 0.3, 0.7, 1.0])
        rng = np.random.default_rng(42)
        angles = rng.standard_normal((4, 3))
        n_frames = 10

        result = pinocchio_models_core.interpolate_phases_rs(fracs, angles, n_frames)
        ref = _interpolate_ref(fracs, angles, n_frames)
        np.testing.assert_allclose(result, ref, atol=1e-10)
