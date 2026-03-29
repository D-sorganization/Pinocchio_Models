"""Gait optimization objective."""

from pinocchio_models.optimization.objectives.common import (
    ExerciseObjective,
    Phase,
    _rad,
)

GAIT_OBJECTIVE = ExerciseObjective(
    name="gait",
    start_pose={
        "hip_l_flex": _rad(30),
        "hip_r_flex": _rad(-10),
        "knee_l_flex": 0.0,
        "knee_r_flex": _rad(-40),
        "ankle_l_flex": _rad(-15),
        "ankle_r_flex": _rad(-20),
    },
    end_pose={
        "hip_l_flex": _rad(30),
        "hip_r_flex": _rad(-10),
        "knee_l_flex": 0.0,
        "knee_r_flex": _rad(-40),
        "ankle_l_flex": _rad(-15),
        "ankle_r_flex": _rad(-20),
    },
    phases=(
        Phase(
            "heel_strike",
            0.0,
            {
                "hip_l_flex": _rad(30),
                "knee_l_flex": 0.0,
                "ankle_l_flex": _rad(-15),
                "hip_r_flex": _rad(-10),
                "knee_r_flex": _rad(-40),
                "ankle_r_flex": _rad(-20),
            },
        ),
        Phase(
            "loading_response",
            0.12,
            {
                "hip_l_flex": _rad(25),
                "knee_l_flex": _rad(-15),
                "ankle_l_flex": _rad(-10),
                "hip_r_flex": _rad(-10),
                "knee_r_flex": _rad(-40),
                "ankle_r_flex": _rad(-25),
            },
        ),
        Phase(
            "mid_stance",
            0.30,
            {
                "hip_l_flex": _rad(5),
                "knee_l_flex": _rad(-5),
                "ankle_l_flex": _rad(10),
                "hip_r_flex": _rad(5),
                "knee_r_flex": _rad(-5),
                "ankle_r_flex": 0.0,
            },
        ),
        Phase(
            "terminal_stance",
            0.50,
            {
                "hip_l_flex": _rad(-10),
                "knee_l_flex": 0.0,
                "ankle_l_flex": _rad(15),
                "hip_r_flex": _rad(20),
                "knee_r_flex": 0.0,
                "ankle_r_flex": _rad(-5),
            },
        ),
        Phase(
            "pre_swing",
            0.62,
            {
                "hip_l_flex": _rad(-10),
                "knee_l_flex": _rad(-40),
                "ankle_l_flex": _rad(-20),
                "hip_r_flex": _rad(30),
                "knee_r_flex": 0.0,
                "ankle_r_flex": _rad(-15),
            },
        ),
        Phase(
            "initial_swing",
            0.75,
            {
                "hip_l_flex": _rad(15),
                "knee_l_flex": _rad(-60),
                "ankle_l_flex": _rad(-5),
                "hip_r_flex": _rad(25),
                "knee_r_flex": _rad(-15),
                "ankle_r_flex": _rad(-10),
            },
        ),
        Phase(
            "mid_swing",
            0.87,
            {
                "hip_l_flex": _rad(25),
                "knee_l_flex": _rad(-30),
                "ankle_l_flex": 0.0,
                "hip_r_flex": _rad(5),
                "knee_r_flex": _rad(-5),
                "ankle_r_flex": _rad(10),
            },
        ),
        Phase(
            "terminal_swing",
            1.0,
            {
                "hip_l_flex": _rad(30),
                "knee_l_flex": 0.0,
                "ankle_l_flex": _rad(-15),
                "hip_r_flex": _rad(-10),
                "knee_r_flex": _rad(-40),
                "ankle_r_flex": _rad(-20),
            },
        ),
    ),
    bar_path_constraint="vertical",
    balance_mode="bilateral_stance",
)
