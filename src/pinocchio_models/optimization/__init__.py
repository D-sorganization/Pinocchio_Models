"""Optimization objectives and trajectory tools for barbell movements."""

from pinocchio_models.optimization.exercise_objectives import (
    EXERCISE_OBJECTIVES,
    ExerciseObjective,
    Phase,
    get_exercise_objective,
)
from pinocchio_models.optimization.trajectory_optimizer import (
    TrajectoryConfig,
    TrajectoryResult,
    interpolate_phases,
)

__all__ = [
    "EXERCISE_OBJECTIVES",
    "ExerciseObjective",
    "Phase",
    "TrajectoryConfig",
    "TrajectoryResult",
    "get_exercise_objective",
    "interpolate_phases",
]
