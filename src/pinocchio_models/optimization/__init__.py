"""Optimization objectives and trajectory tools for barbell movements."""

from pinocchio_models.optimization.exercise_objectives import (  # noqa: I001
    ExerciseObjective,
    Phase,
    get_exercise_objective,
    EXERCISE_OBJECTIVES,
)
from pinocchio_models.optimization.trajectory_optimizer import (
    TrajectoryConfig,
    TrajectoryResult,
    interpolate_phases,
)

__all__ = [
    "ExerciseObjective",
    "Phase",
    "get_exercise_objective",
    "EXERCISE_OBJECTIVES",
    "TrajectoryConfig",
    "TrajectoryResult",
    "interpolate_phases",
]
