"""Deadlift optimization objective."""

from pinocchio_models.optimization.objectives.common import (
    ExerciseObjective,
    Phase,
    _rad,
)

DEADLIFT_OBJECTIVE = ExerciseObjective(
    name="deadlift",
    start_pose={
        "hip_l_flex": _rad(80),
        "hip_r_flex": _rad(80),
        "knee_l_flex": _rad(-70),
        "knee_r_flex": _rad(-70),
        "ankle_l_flex": _rad(20),
        "ankle_r_flex": _rad(20),
        "lumbar_flex": _rad(10),
    },
    end_pose={
        "hip_l_flex": 0.0,
        "hip_r_flex": 0.0,
        "knee_l_flex": 0.0,
        "knee_r_flex": 0.0,
        "ankle_l_flex": 0.0,
        "ankle_r_flex": 0.0,
        "lumbar_flex": 0.0,
    },
    phases=(
        Phase(
            "floor",
            0.0,
            {
                "hip_l_flex": _rad(80),
                "knee_l_flex": _rad(-70),
                "ankle_l_flex": _rad(20),
                "lumbar_flex": _rad(10),
            },
        ),
        Phase(
            "break_floor",
            0.2,
            {
                "hip_l_flex": _rad(65),
                "knee_l_flex": _rad(-50),
                "ankle_l_flex": _rad(15),
                "lumbar_flex": _rad(8),
            },
        ),
        Phase(
            "knee_pass",
            0.5,
            {
                "hip_l_flex": _rad(40),
                "knee_l_flex": _rad(-20),
                "ankle_l_flex": _rad(5),
                "lumbar_flex": _rad(5),
            },
        ),
        Phase(
            "lockout",
            1.0,
            {
                "hip_l_flex": 0.0,
                "knee_l_flex": 0.0,
                "ankle_l_flex": 0.0,
                "lumbar_flex": 0.0,
            },
        ),
    ),
    bar_path_constraint="vertical",
    balance_mode="bilateral_stance",
)
