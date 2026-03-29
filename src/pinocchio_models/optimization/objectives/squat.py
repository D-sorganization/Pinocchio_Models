"""Back squat optimization objective."""

from pinocchio_models.optimization.objectives.common import (
    ExerciseObjective,
    Phase,
    _rad,
)

SQUAT_OBJECTIVE = ExerciseObjective(
    name="back_squat",
    start_pose={
        "hip_l_flex": 0.0,
        "hip_r_flex": 0.0,
        "knee_l_flex": 0.0,
        "knee_r_flex": 0.0,
        "ankle_l_flex": 0.0,
        "ankle_r_flex": 0.0,
        "lumbar_flex": 0.0,
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
        Phase("start", 0.0, {"hip_l_flex": 0.0, "knee_l_flex": 0.0}),
        Phase(
            "descent",
            0.25,
            {
                "hip_l_flex": _rad(60),
                "knee_l_flex": _rad(-60),
                "ankle_l_flex": _rad(25),
            },
        ),
        Phase(
            "bottom",
            0.5,
            {
                "hip_l_flex": _rad(120),
                "knee_l_flex": _rad(-120),
                "ankle_l_flex": _rad(35),
                "lumbar_flex": _rad(15),
            },
        ),
        Phase(
            "drive",
            0.75,
            {"hip_l_flex": _rad(60), "knee_l_flex": _rad(-60)},
        ),
        Phase("lockout", 1.0, {"hip_l_flex": 0.0, "knee_l_flex": 0.0}),
    ),
    bar_path_constraint="vertical",
    balance_mode="bilateral_stance",
)
