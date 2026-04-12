"""Keyframe phase tables used by the Pink IK exercise keyframe generator.

Separated from :mod:`ik_solver` so the data tables can evolve without
bloating the IK orchestration module. Re-exported from the facade for
backward compatibility.
"""

from __future__ import annotations

# Exercise phase definitions for keyframe generation.
# Maps exercise_name -> list of (phase_name, hip_angle_fraction) pairs
# where fraction 0.0 = start position, 1.0 = end position.
_EXERCISE_PHASES: dict[str, list[tuple[str, float]]] = {
    "back_squat": [
        ("standing", 0.0),
        ("descent_start", 0.2),
        ("quarter_squat", 0.4),
        ("half_squat", 0.6),
        ("parallel", 0.8),
        ("bottom", 1.0),
        ("ascent_start", 0.8),
        ("half_up", 0.5),
        ("quarter_up", 0.25),
        ("lockout", 0.0),
    ],
    "bench_press": [
        ("lockout", 0.0),
        ("descent_start", 0.15),
        ("mid_descent", 0.4),
        ("chest_touch", 1.0),
        ("press_start", 0.9),
        ("mid_press", 0.5),
        ("near_lockout", 0.15),
        ("lockout_end", 0.0),
    ],
    "deadlift": [
        ("floor", 1.0),
        ("break_floor", 0.85),
        ("below_knee", 0.6),
        ("above_knee", 0.4),
        ("hip_drive", 0.2),
        ("lockout", 0.0),
    ],
    "snatch": [
        ("floor", 1.0),
        ("first_pull", 0.7),
        ("power_position", 0.3),
        ("triple_ext", 0.0),
        ("turnover", 0.5),
        ("overhead_squat", 0.9),
        ("recovery", 0.0),
    ],
    "clean_and_jerk": [
        ("floor", 1.0),
        ("first_pull", 0.7),
        ("power_position", 0.3),
        ("rack", 0.1),
        ("dip", 0.3),
        ("drive", 0.0),
        ("split", 0.2),
        ("recovery", 0.0),
    ],
}
