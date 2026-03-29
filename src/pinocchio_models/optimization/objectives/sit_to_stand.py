"""Sit-to-stand optimization objective."""

from pinocchio_models.optimization.objectives.common import (
    ExerciseObjective,
    Phase,
    _rad,
)

SIT_TO_STAND_OBJECTIVE = ExerciseObjective(
    name="sit_to_stand",
    start_pose={
        "hip_l_flex": _rad(90),
        "hip_r_flex": _rad(90),
        "knee_l_flex": _rad(-90),
        "knee_r_flex": _rad(-90),
        "ankle_l_flex": _rad(15),
        "ankle_r_flex": _rad(15),
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
            "seated",
            0.0,
            {
                "hip_l_flex": _rad(90),
                "knee_l_flex": _rad(-90),
                "ankle_l_flex": _rad(15),
                "lumbar_flex": _rad(10),
            },
        ),
        Phase(
            "weight_shift",
            0.15,
            {
                "hip_l_flex": _rad(100),
                "knee_l_flex": _rad(-85),
                "ankle_l_flex": _rad(20),
                "lumbar_flex": _rad(30),
            },
        ),
        Phase(
            "seat_off",
            0.35,
            {
                "hip_l_flex": _rad(80),
                "knee_l_flex": _rad(-80),
                "ankle_l_flex": _rad(20),
                "lumbar_flex": _rad(25),
            },
        ),
        Phase(
            "momentum_transfer",
            0.55,
            {
                "hip_l_flex": _rad(50),
                "knee_l_flex": _rad(-50),
                "ankle_l_flex": _rad(10),
                "lumbar_flex": _rad(15),
            },
        ),
        Phase(
            "extension",
            0.80,
            {
                "hip_l_flex": _rad(20),
                "knee_l_flex": _rad(-20),
                "ankle_l_flex": _rad(5),
                "lumbar_flex": _rad(5),
            },
        ),
        Phase(
            "standing",
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
