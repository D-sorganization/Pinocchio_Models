"""Exercise-specific optimization objectives for barbell movements.

This module is a backward-compatibility shim.  The objective data has been
split into per-exercise modules under ``optimization/objectives/``.  All
public names are re-exported here so that existing imports continue to work.
"""

from pinocchio_models.optimization.objectives.bench_press import (  # noqa: F401
    BENCH_PRESS_OBJECTIVE,
)
from pinocchio_models.optimization.objectives.clean_and_jerk import (  # noqa: F401
    CLEAN_AND_JERK_OBJECTIVE,
)
from pinocchio_models.optimization.objectives.common import (  # noqa: F401
    ExerciseObjective,
    Phase,
    _rad,
)
from pinocchio_models.optimization.objectives.deadlift import (  # noqa: F401
    DEADLIFT_OBJECTIVE,
)
from pinocchio_models.optimization.objectives.gait import GAIT_OBJECTIVE  # noqa: F401
from pinocchio_models.optimization.objectives.registry import (  # noqa: F401
    EXERCISE_OBJECTIVES,
    get_exercise_objective,
)
from pinocchio_models.optimization.objectives.sit_to_stand import (  # noqa: F401
    SIT_TO_STAND_OBJECTIVE,
)
from pinocchio_models.optimization.objectives.snatch import (  # noqa: F401
    SNATCH_OBJECTIVE,
)
from pinocchio_models.optimization.objectives.squat import (  # noqa: F401
    SQUAT_OBJECTIVE,
)
