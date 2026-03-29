"""Bench press optimization objective."""

from pinocchio_models.optimization.objectives.common import (
    ExerciseObjective,
    Phase,
    _rad,
)

BENCH_PRESS_OBJECTIVE = ExerciseObjective(
    name="bench_press",
    start_pose={
        "shoulder_l_flex": _rad(90),
        "shoulder_r_flex": _rad(90),
        "elbow_l_flex": 0.0,
        "elbow_r_flex": 0.0,
    },
    end_pose={
        "shoulder_l_flex": _rad(90),
        "shoulder_r_flex": _rad(90),
        "elbow_l_flex": 0.0,
        "elbow_r_flex": 0.0,
    },
    phases=(
        Phase(
            "lockout_top",
            0.0,
            {"shoulder_l_flex": _rad(90), "elbow_l_flex": 0.0},
        ),
        Phase(
            "descent",
            0.25,
            {"shoulder_l_flex": _rad(45), "elbow_l_flex": _rad(45)},
        ),
        Phase(
            "chest",
            0.5,
            {"shoulder_l_flex": _rad(0), "elbow_l_flex": _rad(90)},
        ),
        Phase(
            "drive",
            0.75,
            {"shoulder_l_flex": _rad(45), "elbow_l_flex": _rad(45)},
        ),
        Phase(
            "lockout_finish",
            1.0,
            {"shoulder_l_flex": _rad(90), "elbow_l_flex": 0.0},
        ),
    ),
    bar_path_constraint="j_curve",
    balance_mode="supine",
)
