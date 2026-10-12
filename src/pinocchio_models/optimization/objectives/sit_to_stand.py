"""Sit-to-stand optimization objective.

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

_SIT_TO_STAND_TARGETS: dict[str, dict[str, float]] = {
    "seated": {
        "hip_l_flex": _rad(90),
        "knee_l_flex": _rad(-90),
        "ankle_l_flex": _rad(15),
        "lumbar_flex": _rad(10),
    },
    "trunk_flexion": {
        "hip_l_flex": _rad(100),
        "knee_l_flex": _rad(-85),
        "ankle_l_flex": _rad(20),
        "lumbar_flex": _rad(30),
    },
    "seat_off": {
        "hip_l_flex": _rad(80),
        "knee_l_flex": _rad(-80),
        "ankle_l_flex": _rad(20),
        "lumbar_flex": _rad(25),
    },
    "rising": {
        "hip_l_flex": _rad(50),
        "knee_l_flex": _rad(-50),
        "ankle_l_flex": _rad(10),
        "lumbar_flex": _rad(15),
    },
    "extension_end": {
        "hip_l_flex": _rad(20),
        "knee_l_flex": _rad(-20),
        "ankle_l_flex": _rad(5),
        "lumbar_flex": _rad(5),
    },
    "stabilisation": {
        "hip_l_flex": 0.0,
        "knee_l_flex": 0.0,
        "ankle_l_flex": 0.0,
        "lumbar_flex": 0.0,
    },
}

_PHASES: tuple[Phase, ...] = tuple(
    Phase(
        str(p["name"]),
        float(p["t_frac"]),
        _SIT_TO_STAND_TARGETS[str(p["name"])],
    )
    for p in spec.exercise_spec(STANDARD, "sit_to_stand")["phases"]
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
    phases=_PHASES,
    bar_path_constraint="vertical",
    balance_mode="bilateral_stance",
)
