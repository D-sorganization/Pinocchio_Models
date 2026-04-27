"""Central registry of all exercise objectives."""

from __future__ import annotations

from pinocchio_models.optimization.objectives.bench_press import (
    BENCH_PRESS_OBJECTIVE,
)
from pinocchio_models.optimization.objectives.clean_and_jerk import (
    CLEAN_AND_JERK_OBJECTIVE,
)
from pinocchio_models.optimization.objectives.common import ExerciseObjective
from pinocchio_models.optimization.objectives.deadlift import DEADLIFT_OBJECTIVE
from pinocchio_models.optimization.objectives.gait import GAIT_OBJECTIVE
from pinocchio_models.optimization.objectives.sit_to_stand import (
    SIT_TO_STAND_OBJECTIVE,
)
from pinocchio_models.optimization.objectives.snatch import SNATCH_OBJECTIVE
from pinocchio_models.optimization.objectives.squat import SQUAT_OBJECTIVE
from pinocchio_models.exceptions import GeometryError

EXERCISE_OBJECTIVES: dict[str, ExerciseObjective] = {
    "back_squat": SQUAT_OBJECTIVE,
    "deadlift": DEADLIFT_OBJECTIVE,
    "bench_press": BENCH_PRESS_OBJECTIVE,
    "snatch": SNATCH_OBJECTIVE,
    "clean_and_jerk": CLEAN_AND_JERK_OBJECTIVE,
    "gait": GAIT_OBJECTIVE,
    "sit_to_stand": SIT_TO_STAND_OBJECTIVE,
}


def get_exercise_objective(name: str) -> ExerciseObjective:
    """Return the named exercise objective or raise GeometryError."""
    if name not in EXERCISE_OBJECTIVES:
        raise GeometryError(
            f"Unknown exercise: {name}. Available: {list(EXERCISE_OBJECTIVES)}"
        )
    return EXERCISE_OBJECTIVES[name]