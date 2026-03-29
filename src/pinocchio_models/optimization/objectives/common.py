"""Shared data structures for exercise optimization objectives."""

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
    """Convert degrees to radians."""
    return math.radians(deg)
