"""Snatch model builder (URDF for Pinocchio).

The snatch is a single continuous movement lifting the barbell from
the ground to overhead in one motion. The barbell is gripped with a
wide (snatch) grip and welded to the hands.

Biomechanical notes:
- Primary movers: full posterior chain, deltoids, trapezius
- Three phases: first pull, second pull (triple extension), overhead squat
- Wide grip reduces the vertical distance the bar must travel
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.base import ExerciseConfig, ExerciseModelBuilder
from pinocchio_models.shared.constants import (
    SNATCH_GRIP_FRACTION,
    SNATCH_HIP_ANGLE,
    SNATCH_KNEE_ANGLE,
    SNATCH_LUMBAR_ANGLE,
)


class SnatchModelBuilder(ExerciseModelBuilder):
    """Builds a snatch URDF model for Pinocchio.

    The barbell is welded to both hands at a wide (snatch) grip width.
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        super().__init__(config)

    @property
    def exercise_name(self) -> str:
        return "snatch"

    @property
    def grip_offset_fraction(self) -> float:
        return SNATCH_GRIP_FRACTION

    def set_initial_pose(self, robot: ET.Element) -> None:
        """Set starting position: crouched over bar.

        Hips flexed ~80 deg, knees ~70 deg, slight lumbar extension.
        """
        _set_joint_default(robot, "hip", SNATCH_HIP_ANGLE)
        _set_joint_default(robot, "knee", SNATCH_KNEE_ANGLE)
        _set_joint_default(robot, "lumbar", SNATCH_LUMBAR_ANGLE)


def _set_joint_default(robot: ET.Element, prefix: str, value: float) -> None:
    """Set the default position of joints via initial_position attribute."""
    for joint in robot.findall("joint"):
        name = joint.get("name", "")
        if name == prefix or name.startswith(f"{prefix}_"):
            joint.set("initial_position", f"{value:.6f}")


def build_snatch_model(
    body_mass: float = 80.0,
    height: float = 1.75,
    plate_mass_per_side: float = 40.0,
) -> str:
    """Convenience function to build a snatch URDF string.

    Default: 80 kg person, 1.75 m tall, 100 kg total barbell.
    """
    from pinocchio_models.shared.barbell import BarbellSpec
    from pinocchio_models.shared.body import BodyModelSpec

    config = ExerciseConfig(
        body_spec=BodyModelSpec(total_mass=body_mass, height=height),
        barbell_spec=BarbellSpec.mens_olympic(plate_mass_per_side=plate_mass_per_side),
    )
    return SnatchModelBuilder(config).build()
