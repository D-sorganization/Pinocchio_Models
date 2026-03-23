"""Clean and jerk model builder (URDF for Pinocchio).

The clean and jerk is a two-phase Olympic lift: the clean brings the
barbell from the ground to the front rack position, and the jerk drives
it overhead. The barbell is gripped at shoulder width.

Biomechanical notes:
- Clean primary movers: posterior chain, quadriceps, upper back
- Jerk primary movers: quadriceps, deltoids, triceps
- Front rack position requires adequate wrist/shoulder mobility
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.base import ExerciseConfig, ExerciseModelBuilder
from pinocchio_models.shared.constants import (
    CLEAN_AND_JERK_GRIP_FRACTION,
    CLEAN_AND_JERK_HIP_ANGLE,
    CLEAN_AND_JERK_KNEE_ANGLE,
    CLEAN_AND_JERK_LUMBAR_ANGLE,
)


class CleanAndJerkModelBuilder(ExerciseModelBuilder):
    """Builds a clean-and-jerk URDF model for Pinocchio.

    The barbell is welded to both hands at shoulder-width grip.
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        super().__init__(config)

    @property
    def exercise_name(self) -> str:
        return "clean_and_jerk"

    @property
    def grip_offset_fraction(self) -> float:
        return CLEAN_AND_JERK_GRIP_FRACTION

    def set_initial_pose(self, robot: ET.Element) -> None:
        """Set starting position: crouched over bar.

        Hips flexed ~75 deg, knees ~65 deg, slight lumbar extension.
        """
        _set_joint_default(robot, "hip", CLEAN_AND_JERK_HIP_ANGLE)
        _set_joint_default(robot, "knee", CLEAN_AND_JERK_KNEE_ANGLE)
        _set_joint_default(robot, "lumbar", CLEAN_AND_JERK_LUMBAR_ANGLE)


def _set_joint_default(robot: ET.Element, prefix: str, value: float) -> None:
    """Set the default position of joints via initial_position attribute."""
    for joint in robot.findall("joint"):
        name = joint.get("name", "")
        if name == prefix or name.startswith(f"{prefix}_"):
            joint.set("initial_position", f"{value:.6f}")


def build_clean_and_jerk_model(
    body_mass: float = 80.0,
    height: float = 1.75,
    plate_mass_per_side: float = 50.0,
) -> str:
    """Convenience function to build a clean-and-jerk URDF string.

    Default: 80 kg person, 1.75 m tall, 120 kg total barbell.
    """
    from pinocchio_models.shared.barbell import BarbellSpec
    from pinocchio_models.shared.body import BodyModelSpec

    config = ExerciseConfig(
        body_spec=BodyModelSpec(total_mass=body_mass, height=height),
        barbell_spec=BarbellSpec.mens_olympic(plate_mass_per_side=plate_mass_per_side),
    )
    return CleanAndJerkModelBuilder(config).build()
