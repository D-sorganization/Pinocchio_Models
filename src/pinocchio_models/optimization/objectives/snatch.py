"""Snatch optimization objective."""

from pinocchio_models.optimization.objectives.common import (
    ExerciseObjective,
    Phase,
    _rad,
)

SNATCH_OBJECTIVE = ExerciseObjective(
    name="snatch",
    start_pose={
        "hip_l_flex": _rad(80),
        "hip_r_flex": _rad(80),
        "knee_l_flex": _rad(-70),
        "knee_r_flex": _rad(-70),
        "shoulder_l_flex": _rad(0),
        "shoulder_r_flex": _rad(0),
        "elbow_l_flex": 0.0,
        "elbow_r_flex": 0.0,
    },
    end_pose={
        "hip_l_flex": _rad(120),
        "hip_r_flex": _rad(120),
        "knee_l_flex": _rad(-120),
        "knee_r_flex": _rad(-120),
        "shoulder_l_flex": _rad(180),
        "shoulder_r_flex": _rad(180),
        "elbow_l_flex": 0.0,
        "elbow_r_flex": 0.0,
    },
    phases=(
        Phase(
            "first_pull",
            0.0,
            {
                "hip_l_flex": _rad(80),
                "knee_l_flex": _rad(-70),
                "shoulder_l_flex": _rad(0),
                "elbow_l_flex": 0.0,
            },
        ),
        Phase(
            "transition",
            0.2,
            {
                "hip_l_flex": _rad(50),
                "knee_l_flex": _rad(-40),
                "shoulder_l_flex": _rad(20),
                "elbow_l_flex": 0.0,
            },
        ),
        Phase(
            "second_pull",
            0.4,
            {
                "hip_l_flex": _rad(10),
                "knee_l_flex": _rad(-10),
                "shoulder_l_flex": _rad(70),
                "elbow_l_flex": _rad(30),
            },
        ),
        Phase(
            "turnover",
            0.6,
            {
                "hip_l_flex": _rad(60),
                "knee_l_flex": _rad(-60),
                "shoulder_l_flex": _rad(150),
                "elbow_l_flex": _rad(20),
            },
        ),
        Phase(
            "catch",
            0.8,
            {
                "hip_l_flex": _rad(120),
                "knee_l_flex": _rad(-120),
                "shoulder_l_flex": _rad(180),
                "elbow_l_flex": 0.0,
            },
        ),
        Phase(
            "recovery",
            1.0,
            {
                "hip_l_flex": 0.0,
                "knee_l_flex": 0.0,
                "shoulder_l_flex": _rad(180),
                "elbow_l_flex": 0.0,
            },
        ),
    ),
    bar_path_constraint="s_curve",
    balance_mode="bilateral_stance",
)
