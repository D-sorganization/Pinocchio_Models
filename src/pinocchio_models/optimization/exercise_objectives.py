"""Exercise-specific optimization objectives for barbell movements."""

from __future__ import annotations

import math
from dataclasses import dataclass


@dataclass(frozen=True)
class Phase:
    """A single phase within an exercise movement."""

    name: str
    fraction: float  # 0.0 to 1.0
    target_joints: dict[str, float]  # joint_name -> angle in radians


@dataclass(frozen=True)
class ExerciseObjective:
    """Full optimization objective for an exercise."""

    name: str
    start_pose: dict[str, float]
    end_pose: dict[str, float]
    phases: tuple[Phase, ...]
    bar_path_constraint: str  # "vertical", "j_curve", "s_curve"
    balance_mode: str  # "bilateral_stance", "split_stance", "supine"


def _rad(deg: float) -> float:
    return math.radians(deg)


# ---------------------------------------------------------------------------
# Back Squat
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Conventional Deadlift
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Bench Press
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Snatch (6 phases)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Clean & Jerk (8 phases: 4 clean + 4 jerk)
# ---------------------------------------------------------------------------
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

# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------
EXERCISE_OBJECTIVES: dict[str, ExerciseObjective] = {
    "back_squat": SQUAT_OBJECTIVE,
    "deadlift": DEADLIFT_OBJECTIVE,
    "bench_press": BENCH_PRESS_OBJECTIVE,
    "snatch": SNATCH_OBJECTIVE,
    "clean_and_jerk": CLEAN_AND_JERK_OBJECTIVE,
}


def get_exercise_objective(name: str) -> ExerciseObjective:
    """Return the named exercise objective or raise ValueError."""
    if name not in EXERCISE_OBJECTIVES:
        raise ValueError(
            f"Unknown exercise: {name}. Available: {list(EXERCISE_OBJECTIVES)}"
        )
    return EXERCISE_OBJECTIVES[name]
