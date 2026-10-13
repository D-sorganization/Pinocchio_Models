"""Engine-independent penalty contact and integrator stability (issue #430)."""

from __future__ import annotations

import numpy as np
import pytest

from pinocchio_models.shared.contact.penalty import (
    DEFAULT_STATIC_PENETRATION_M,
    PenaltyContactParams,
    integrator_spectral_radius,
    max_stable_time_step,
    penalty_contact_force,
    penalty_contact_params,
)

G = 9.80665
PARAMS = PenaltyContactParams(stiffness=1e4, damping=100.0, tangential_damping=50.0)


def _oscillator(omega: float, zeta: float, mass: float = 2.0) -> tuple:
    k = mass * omega**2
    c = 2.0 * zeta * mass * omega
    return np.array([[mass]]), np.array([[k]]), np.array([[c]])


class TestPenaltyContactParams:
    def test_static_penetration_and_mode_frequency(self) -> None:
        weight, n, delta = 800.0, 8, 2e-3
        p = penalty_contact_params(weight, n, static_penetration_m=delta, gravity=G)

        assert weight / (n * p.stiffness) == pytest.approx(delta)
        mass = weight / G
        omega = np.sqrt(n * p.stiffness / mass)
        assert omega == pytest.approx(np.sqrt(G / delta))
        zeta = n * p.damping / (2.0 * mass * omega)
        assert zeta == pytest.approx(1.0)
        assert p.tangential_damping == p.damping

    def test_damping_ratio_scales_damping(self) -> None:
        crit = penalty_contact_params(800.0, 8, damping_ratio=1.0)
        half = penalty_contact_params(800.0, 8, damping_ratio=0.5)
        assert half.damping == pytest.approx(0.5 * crit.damping)
        assert half.stiffness == crit.stiffness

    def test_default_penetration(self) -> None:
        p = penalty_contact_params(800.0, 8)
        assert 800.0 / (8 * p.stiffness) == pytest.approx(DEFAULT_STATIC_PENETRATION_M)

    @pytest.mark.parametrize(
        ("kwargs", "match"),
        [
            ({"weight_n": 0.0}, "weight_n"),
            ({"n_points": 0}, "n_points"),
            ({"static_penetration_m": 0.0}, "static_penetration_m"),
            ({"damping_ratio": -1.0}, "damping_ratio"),
            ({"gravity": 0.0}, "gravity"),
        ],
    )
    def test_preconditions(self, kwargs: dict, match: str) -> None:
        args = {"weight_n": 800.0, "n_points": 8} | kwargs
        with pytest.raises(ValueError, match=match):
            penalty_contact_params(**args)

    def test_dataclass_rejects_bad_gains(self) -> None:
        with pytest.raises(ValueError, match="stiffness"):
            PenaltyContactParams(stiffness=0.0, damping=1.0, tangential_damping=1.0)
        with pytest.raises(ValueError, match="tangential_damping"):
            PenaltyContactParams(stiffness=1.0, damping=1.0, tangential_damping=-1.0)


class TestPenaltyContactForce:
    def test_no_force_above_floor(self) -> None:
        f = penalty_contact_force([0, 0, 1e-4], [0, 0, -1.0], 0.8, PARAMS)
        np.testing.assert_array_equal(f, np.zeros(3))

    def test_spring_force_at_rest(self) -> None:
        f = penalty_contact_force([0.1, 0.2, -1e-3], np.zeros(3), 0.8, PARAMS)
        np.testing.assert_allclose(f, [0.0, 0.0, PARAMS.stiffness * 1e-3])

    def test_damping_adds_on_approach(self) -> None:
        f = penalty_contact_force([0, 0, -1e-3], [0, 0, -0.1], 0.8, PARAMS)
        assert f[2] == pytest.approx(10.0 + 10.0)

    def test_floor_never_pulls(self) -> None:
        f = penalty_contact_force([0, 0, -1e-3], [0, 0, 10.0], 0.8, PARAMS)
        np.testing.assert_array_equal(f, np.zeros(3))

    def test_viscous_friction_inside_cone(self) -> None:
        f = penalty_contact_force([0, 0, -1e-2], [0.01, -0.02, 0.0], 0.8, PARAMS)
        np.testing.assert_allclose(f[:2], [-0.5, 1.0])

    def test_friction_clipped_to_coulomb_cone(self) -> None:
        f = penalty_contact_force([0, 0, -1e-3], [3.0, 4.0, 0.0], 0.5, PARAMS)
        assert np.hypot(f[0], f[1]) == pytest.approx(0.5 * f[2])
        np.testing.assert_allclose(f[:2] / np.hypot(f[0], f[1]), [-0.6, -0.8])

    def test_ground_height_offset(self) -> None:
        f = penalty_contact_force([0, 0, 0.5], np.zeros(3), 0.8, PARAMS, 0.501)
        assert f[2] == pytest.approx(PARAMS.stiffness * 1e-3)

    def test_preconditions(self) -> None:
        with pytest.raises(ValueError, match="position"):
            penalty_contact_force([0, 0], np.zeros(3), 0.8, PARAMS)
        with pytest.raises(ValueError, match="non-finite"):
            penalty_contact_force([0, 0, np.nan], np.zeros(3), 0.8, PARAMS)
        with pytest.raises(ValueError, match="mu"):
            penalty_contact_force(np.zeros(3), np.zeros(3), -0.1, PARAMS)


class TestStability:
    @pytest.mark.parametrize("zeta", [0.0, 0.5, 1.0, 2.0])
    def test_single_oscillator_matches_closed_form(self, zeta: float) -> None:
        omega = 70.0
        m, k, c = _oscillator(omega, zeta)
        expected = 2.0 * (zeta + np.sqrt(1.0 + zeta**2)) / omega

        limit = max_stable_time_step(m, k, c, upper_bound=1.0)

        assert limit == pytest.approx(expected, rel=2e-3)
        assert limit <= expected

    def test_radius_below_and_above_limit(self) -> None:
        m, k, c = _oscillator(10.0, 1.0)
        limit = 2.0 * (1.0 + np.sqrt(2.0)) / 10.0
        assert integrator_spectral_radius(m, k, c, 0.9 * limit) < 1.0
        assert integrator_spectral_radius(m, k, c, 1.1 * limit) > 1.0

    def test_stiffest_mode_sets_the_limit(self) -> None:
        mass = np.diag([1.0, 1.0])
        stiffness = np.diag([1.0, 1e4])
        limit = max_stable_time_step(mass, stiffness, np.zeros((2, 2)), upper_bound=1)
        assert limit == pytest.approx(2.0 / 100.0, rel=2e-3)

    def test_damping_never_destabilises(self) -> None:
        m, k, _ = _oscillator(50.0, 0.0)
        heavy = np.array([[1e9]])
        # Pure (huge) damping: the free-drift position eigenvalue is exactly 1
        # and the velocity one 1 / (1 + dt c / m) -- never unstable.
        radius = integrator_spectral_radius(m, np.zeros((1, 1)), heavy, 1.0)
        assert radius == pytest.approx(1.0, abs=1e-12)
        undamped = max_stable_time_step(m, k, np.zeros((1, 1)), upper_bound=1.0)
        damped = max_stable_time_step(m, k, heavy, upper_bound=1.0)
        assert damped > undamped

    def test_unstiff_system_returns_upper_bound(self) -> None:
        zeros = np.zeros((2, 2))
        assert max_stable_time_step(np.eye(2), zeros, zeros, upper_bound=0.3) == 0.3

    def test_preconditions(self) -> None:
        with pytest.raises(ValueError, match="square"):
            integrator_spectral_radius(np.ones(3), np.ones(3), np.ones(3), 0.1)
        with pytest.raises(ValueError, match="stiffness must have shape"):
            integrator_spectral_radius(np.eye(2), np.eye(3), np.eye(2), 0.1)
        with pytest.raises(ValueError, match="dt"):
            integrator_spectral_radius(np.eye(2), np.eye(2), np.eye(2), 0.0)
        with pytest.raises(np.linalg.LinAlgError):
            integrator_spectral_radius(-np.eye(2), np.eye(2), np.eye(2), 0.1)
        with pytest.raises(ValueError, match="upper_bound"):
            max_stable_time_step(np.eye(1), np.eye(1), np.eye(1), upper_bound=0.0)
