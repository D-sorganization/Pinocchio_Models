"""Tests for exercise-specific optimization objectives."""

import numpy as np
import pytest

from pinocchio_models.optimization.exercise_objectives import (
    EXERCISE_OBJECTIVES,
    ExerciseObjective,
    get_exercise_objective,
)
from pinocchio_models.optimization.trajectory_optimizer import (
    TrajectoryConfig,
    TrajectoryResult,
    _build_phase_arrays,
    _interpolate_keyframes,
    interpolate_phases,
)

EXPECTED_EXERCISES = [
    "back_squat",
    "deadlift",
    "bench_press",
    "snatch",
    "clean_and_jerk",
    "gait",
    "sit_to_stand",
]


# ------------------------------------------------------------------
# ExerciseObjective validity
# ------------------------------------------------------------------
class TestExerciseObjectives:
    @pytest.mark.parametrize("name", EXPECTED_EXERCISES)
    def test_objective_exists(self, name: str) -> None:
        obj = EXERCISE_OBJECTIVES[name]
        assert isinstance(obj, ExerciseObjective)
        assert obj.name == name

    @pytest.mark.parametrize("name", EXPECTED_EXERCISES)
    def test_phases_fractions_monotonic(self, name: str) -> None:
        obj = EXERCISE_OBJECTIVES[name]
        fractions = [p.fraction for p in obj.phases]
        for i in range(len(fractions) - 1):
            assert fractions[i] < fractions[i + 1], (
                f"{name}: phase fractions not monotonically increasing at index {i}"
            )

    @pytest.mark.parametrize("name", EXPECTED_EXERCISES)
    def test_phases_fractions_in_range(self, name: str) -> None:
        obj = EXERCISE_OBJECTIVES[name]
        for phase in obj.phases:
            assert 0.0 <= phase.fraction <= 1.0, (
                f"{name}/{phase.name}: fraction {phase.fraction} out of [0, 1]"
            )

    @pytest.mark.parametrize("name", EXPECTED_EXERCISES)
    def test_first_phase_starts_at_zero(self, name: str) -> None:
        obj = EXERCISE_OBJECTIVES[name]
        assert obj.phases[0].fraction == 0.0

    @pytest.mark.parametrize("name", EXPECTED_EXERCISES)
    def test_last_phase_ends_at_one(self, name: str) -> None:
        obj = EXERCISE_OBJECTIVES[name]
        assert obj.phases[-1].fraction == 1.0


# ------------------------------------------------------------------
# get_exercise_objective
# ------------------------------------------------------------------
class TestGetExerciseObjective:
    @pytest.mark.parametrize("name", EXPECTED_EXERCISES)
    def test_returns_correct(self, name: str) -> None:
        obj = get_exercise_objective(name)
        assert obj.name == name

    def test_raises_for_unknown(self) -> None:
        with pytest.raises(ValueError, match="Unknown exercise"):
            get_exercise_objective("nonexistent_exercise")


# ------------------------------------------------------------------
# interpolate_phases
# ------------------------------------------------------------------
class TestInterpolatePhases:
    @pytest.mark.parametrize("name", EXPECTED_EXERCISES)
    def test_output_shape(self, name: str) -> None:
        obj = EXERCISE_OBJECTIVES[name]
        n_frames = 30
        result = interpolate_phases(obj, n_frames=n_frames)
        all_joints: set[str] = set()
        for phase in obj.phases:
            all_joints.update(phase.target_joints.keys())
        assert result.shape == (n_frames, len(all_joints))

    @pytest.mark.parametrize("name", EXPECTED_EXERCISES)
    def test_start_matches_first_phase(self, name: str) -> None:
        obj = EXERCISE_OBJECTIVES[name]
        result = interpolate_phases(obj, n_frames=50)
        all_joints: set[str] = set()
        for phase in obj.phases:
            all_joints.update(phase.target_joints.keys())
        joint_names = sorted(all_joints)
        first_phase = obj.phases[0]
        for k, jname in enumerate(joint_names):
            expected = first_phase.target_joints.get(jname, 0.0)
            np.testing.assert_allclose(
                result[0, k], expected, atol=1e-10, err_msg=f"{name}/{jname} start"
            )

    @pytest.mark.parametrize("name", EXPECTED_EXERCISES)
    def test_end_matches_last_phase(self, name: str) -> None:
        obj = EXERCISE_OBJECTIVES[name]
        result = interpolate_phases(obj, n_frames=50)
        all_joints: set[str] = set()
        for phase in obj.phases:
            all_joints.update(phase.target_joints.keys())
        joint_names = sorted(all_joints)
        last_phase = obj.phases[-1]
        for k, jname in enumerate(joint_names):
            expected = last_phase.target_joints.get(jname, 0.0)
            np.testing.assert_allclose(
                result[-1, k], expected, atol=1e-10, err_msg=f"{name}/{jname} end"
            )


# ------------------------------------------------------------------
# TrajectoryConfig / TrajectoryResult
# ------------------------------------------------------------------
class TestTrajectoryConfig:
    def test_defaults(self) -> None:
        cfg = TrajectoryConfig()
        assert cfg.n_timesteps == 100
        assert cfg.dt == 0.01
        assert cfg.max_iterations == 200
        assert cfg.convergence_tol == 1e-4
        assert cfg.control_weight == 1e-3
        assert cfg.state_weight == 1.0
        assert cfg.terminal_weight == 10.0
        assert cfg.balance_weight == 5.0

    # ------------------------------------------------------------------
    # __post_init__ validation – positive integer fields
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("n_timesteps", [0, -1, -100])
    def test_invalid_n_timesteps_raises(self, n_timesteps: int) -> None:
        with pytest.raises(ValueError, match="n_timesteps"):
            TrajectoryConfig(n_timesteps=n_timesteps)

    @pytest.mark.parametrize("max_iterations", [0, -1, -50])
    def test_invalid_max_iterations_raises(self, max_iterations: int) -> None:
        with pytest.raises(ValueError, match="max_iterations"):
            TrajectoryConfig(max_iterations=max_iterations)

    # ------------------------------------------------------------------
    # __post_init__ validation – positive float fields
    # ------------------------------------------------------------------
    @pytest.mark.parametrize("dt", [0.0, -0.001, -1.0])
    def test_invalid_dt_raises(self, dt: float) -> None:
        with pytest.raises(ValueError, match="dt"):
            TrajectoryConfig(dt=dt)

    @pytest.mark.parametrize("convergence_tol", [0.0, -1e-5, -1.0])
    def test_invalid_convergence_tol_raises(self, convergence_tol: float) -> None:
        with pytest.raises(ValueError, match="convergence_tol"):
            TrajectoryConfig(convergence_tol=convergence_tol)

    # ------------------------------------------------------------------
    # __post_init__ validation – non-negative weight fields
    # ------------------------------------------------------------------
    @pytest.mark.parametrize(
        "field,value",
        [
            ("control_weight", -1e-3),
            ("state_weight", -1.0),
            ("terminal_weight", -10.0),
            ("balance_weight", -5.0),
        ],
    )
    def test_negative_weight_raises(self, field: str, value: float) -> None:
        with pytest.raises(ValueError, match=field):
            TrajectoryConfig(**{field: value})

    # Zero weights are allowed (disabling a cost term is valid)
    @pytest.mark.parametrize(
        "field",
        ["control_weight", "state_weight", "terminal_weight", "balance_weight"],
    )
    def test_zero_weight_accepted(self, field: str) -> None:
        cfg = TrajectoryConfig(**{field: 0.0})
        assert getattr(cfg, field) == 0.0

    # Minimum valid values for strictly-positive fields
    def test_minimum_valid_n_timesteps(self) -> None:
        cfg = TrajectoryConfig(n_timesteps=1)
        assert cfg.n_timesteps == 1

    def test_minimum_valid_max_iterations(self) -> None:
        cfg = TrajectoryConfig(max_iterations=1)
        assert cfg.max_iterations == 1

    def test_minimum_valid_dt(self) -> None:
        cfg = TrajectoryConfig(dt=1e-9)
        assert cfg.dt == pytest.approx(1e-9)

    def test_minimum_valid_convergence_tol(self) -> None:
        cfg = TrajectoryConfig(convergence_tol=1e-12)
        assert cfg.convergence_tol == pytest.approx(1e-12)


class TestTrajectoryResult:
    def test_creation(self) -> None:
        n, nj = 50, 7
        result = TrajectoryResult(
            joint_positions=np.zeros((n, nj)),
            joint_velocities=np.zeros((n, nj)),
            joint_torques=np.zeros((n, nj)),
            time=np.linspace(0, 1, n),
            cost=0.42,
            converged=True,
            iterations=15,
        )
        assert result.converged is True
        assert result.cost == pytest.approx(0.42)
        assert result.joint_positions.shape == (n, nj)


class TestInterpolatePhasesHelpers:
    def test_build_phase_arrays_unions_joint_names(self) -> None:
        objective = get_exercise_objective("back_squat")
        joint_names, phase_fracs, phase_angles = _build_phase_arrays(objective)
        assert joint_names == sorted(joint_names)
        assert phase_fracs.shape == (len(objective.phases),)
        assert phase_angles.shape == (len(objective.phases), len(joint_names))

    def test_interpolate_keyframes_endpoints_match_phases(self) -> None:
        phase_fracs = np.array([0.0, 0.5, 1.0])
        phase_angles = np.array([[0.0, 1.0], [2.0, 3.0], [4.0, 5.0]])
        keyframes = _interpolate_keyframes(phase_fracs, phase_angles, n_frames=5)
        assert keyframes.shape == (5, 2)
        np.testing.assert_allclose(keyframes[0], phase_angles[0])
        np.testing.assert_allclose(keyframes[-1], phase_angles[-1])
