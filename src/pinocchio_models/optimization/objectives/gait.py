"""Gait optimization objective.

Phase names and fractions come from the standard v2.0/v2.1 exercise spec.
"""

from __future__ import annotations

from pinocchio_models.optimization.objectives.common import (
    ExerciseObjective,
    Phase,
    _rad,
)
from pinocchio_models.shared.parity._canonical import conformance, spec

STANDARD = conformance.load_standard()

_GAIT_TARGETS: dict[str, dict[str, float]] = {
    "initial_contact": {
        "hip_l_flex": _rad(30),
        "knee_l_flex": 0.0,
        "ankle_l_flex": _rad(-15),
        "hip_r_flex": _rad(-10),
        "knee_r_flex": _rad(-40),
        "ankle_r_flex": _rad(-20),
    },
    "loading_response": {
        "hip_l_flex": _rad(25),
        "knee_l_flex": _rad(-15),
        "ankle_l_flex": _rad(-10),
        "hip_r_flex": _rad(-10),
        "knee_r_flex": _rad(-40),
        "ankle_r_flex": _rad(-25),
    },
    "mid_stance": {
        "hip_l_flex": _rad(5),
        "knee_l_flex": _rad(-5),
        "ankle_l_flex": _rad(10),
        "hip_r_flex": _rad(5),
        "knee_r_flex": _rad(-5),
        "ankle_r_flex": 0.0,
    },
    "terminal_stance": {
        "hip_l_flex": _rad(-10),
        "knee_l_flex": 0.0,
        "ankle_l_flex": _rad(15),
        "hip_r_flex": _rad(20),
        "knee_r_flex": 0.0,
        "ankle_r_flex": _rad(-5),
    },
    "pre_swing": {
        "hip_l_flex": _rad(-10),
        "knee_l_flex": _rad(-40),
        "ankle_l_flex": _rad(-20),
        "hip_r_flex": _rad(30),
        "knee_r_flex": 0.0,
        "ankle_r_flex": _rad(-15),
    },
    "initial_swing": {
        "hip_l_flex": _rad(15),
        "knee_l_flex": _rad(-60),
        "ankle_l_flex": _rad(-5),
        "hip_r_flex": _rad(25),
        "knee_r_flex": _rad(-15),
        "ankle_r_flex": _rad(-10),
    },
    "mid_swing": {
        "hip_l_flex": _rad(25),
        "knee_l_flex": _rad(-30),
        "ankle_l_flex": 0.0,
        "hip_r_flex": _rad(5),
        "knee_r_flex": _rad(-5),
        "ankle_r_flex": _rad(10),
    },
    "terminal_swing": {
        "hip_l_flex": _rad(30),
        "knee_l_flex": 0.0,
        "ankle_l_flex": _rad(-15),
        "hip_r_flex": _rad(-10),
        "knee_r_flex": _rad(-40),
        "ankle_r_flex": _rad(-20),
    },
}

_PHASES: tuple[Phase, ...] = tuple(
    Phase(
        str(p["name"]),
        float(p["t_frac"]),
        _GAIT_TARGETS[str(p["name"])],
    )
    for p in spec.exercise_spec(STANDARD, "gait")["phases"]
)

GAIT_OBJECTIVE = ExerciseObjective(
    name="gait",
    start_pose=_GAIT_TARGETS["initial_contact"],
    end_pose=_GAIT_TARGETS["terminal_swing"],
    phases=_PHASES,
    bar_path_constraint="vertical",
    balance_mode="bilateral_stance",
)
