"""Per-exercise optimization objective modules.

Each exercise's objective data lives in its own module for maintainability.
The parent ``optimization`` package re-exports everything for backward
compatibility.
"""

from pinocchio_models.optimization.objectives.bench_press import (
    BENCH_PRESS_OBJECTIVE,
)
from pinocchio_models.optimization.objectives.clean_and_jerk import (
    CLEAN_AND_JERK_OBJECTIVE,
)
from pinocchio_models.optimization.objectives.common import (
    ExerciseObjective,
    Phase,
    _rad,
)
from pinocchio_models.optimization.objectives.deadlift import DEADLIFT_OBJECTIVE
from pinocchio_models.optimization.objectives.gait import GAIT_OBJECTIVE
from pinocchio_models.optimization.objectives.registry import (
    EXERCISE_OBJECTIVES,
    get_exercise_objective,
)
from pinocchio_models.optimization.objectives.sit_to_stand import (
    SIT_TO_STAND_OBJECTIVE,
)
from pinocchio_models.optimization.objectives.snatch import SNATCH_OBJECTIVE
from pinocchio_models.optimization.objectives.squat import SQUAT_OBJECTIVE

__all__ = [
    "ExerciseObjective",
    "Phase",
    "_rad",
    "SQUAT_OBJECTIVE",
    "DEADLIFT_OBJECTIVE",
    "BENCH_PRESS_OBJECTIVE",
    "SNATCH_OBJECTIVE",
    "CLEAN_AND_JERK_OBJECTIVE",
    "GAIT_OBJECTIVE",
    "SIT_TO_STAND_OBJECTIVE",
    "EXERCISE_OBJECTIVES",
    "get_exercise_objective",
]
