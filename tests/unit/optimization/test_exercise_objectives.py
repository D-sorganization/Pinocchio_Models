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
    interpolate_phases,
)

EXPECTED_EXERCISES = [
    "back_squat",
    "deadlift",
    "bench_press",
    "snatch",
    "clean_and_jerk",
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
