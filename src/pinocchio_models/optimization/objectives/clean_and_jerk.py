"""Clean and jerk optimization objective."""

from pinocchio_models.optimization.objectives.common import (
    ExerciseObjective,
    Phase,
    _rad,
)

CLEAN_AND_JERK_OBJECTIVE = ExerciseObjective(
    name="clean_and_jerk",
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
        "hip_l_flex": 0.0,
        "hip_r_flex": 0.0,
        "knee_l_flex": 0.0,
        "knee_r_flex": 0.0,
        "shoulder_l_flex": _rad(180),
        "shoulder_r_flex": _rad(180),
        "elbow_l_flex": 0.0,
        "elbow_r_flex": 0.0,
    },
    phases=(
        # Clean phases
        Phase(
            "clean_first_pull",
            0.0,
            {
                "hip_l_flex": _rad(80),
                "knee_l_flex": _rad(-70),
                "shoulder_l_flex": _rad(0),
                "elbow_l_flex": 0.0,
            },
        ),
        Phase(
            "clean_second_pull",
            0.15,
            {
                "hip_l_flex": _rad(10),
                "knee_l_flex": _rad(-10),
                "shoulder_l_flex": _rad(40),
                "elbow_l_flex": _rad(30),
            },
        ),
        Phase(
            "clean_catch",
            0.3,
            {
                "hip_l_flex": _rad(120),
                "knee_l_flex": _rad(-120),
                "shoulder_l_flex": _rad(90),
                "elbow_l_flex": _rad(140),
            },
        ),
        Phase(
            "clean_stand",
            0.45,
            {
                "hip_l_flex": 0.0,
                "knee_l_flex": 0.0,
                "shoulder_l_flex": _rad(90),
                "elbow_l_flex": _rad(140),
            },
        ),
        # Jerk phases
        Phase(
            "jerk_dip",
            0.55,
            {
                "hip_l_flex": _rad(20),
                "knee_l_flex": _rad(-20),
                "shoulder_l_flex": _rad(90),
                "elbow_l_flex": _rad(140),
            },
        ),
        Phase(
            "jerk_drive",
            0.7,
            {
                "hip_l_flex": _rad(5),
                "knee_l_flex": _rad(-5),
                "shoulder_l_flex": _rad(150),
                "elbow_l_flex": _rad(30),
            },
        ),
        Phase(
            "jerk_catch",
            0.85,
            {
                "hip_l_flex": _rad(30),
                "knee_l_flex": _rad(-30),
                "shoulder_l_flex": _rad(180),
                "elbow_l_flex": 0.0,
            },
        ),
        Phase(
            "jerk_recovery",
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
    balance_mode="split_stance",
)
