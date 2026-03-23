"""Deadlift model builder (URDF for Pinocchio).

The athlete grips the barbell with both hands while the bar rests on
the ground. The barbell is welded to both hands via fixed joints.

Biomechanical notes:
- Primary movers: gluteus maximus, hamstrings, erector spinae, quadriceps
- The model captures the hip-hinge pattern in the sagittal plane
- Conventional stance (narrow) is the default
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.base import ExerciseConfig, ExerciseModelBuilder
from pinocchio_models.shared.constants import (
    DEADLIFT_GRIP_FRACTION,
    DEADLIFT_HIP_ANGLE,
    DEADLIFT_KNEE_ANGLE,
    DEADLIFT_LUMBAR_ANGLE,
)


class DeadliftModelBuilder(ExerciseModelBuilder):
    """Builds a deadlift URDF model for Pinocchio.

    The barbell is welded to both hands at approximately shoulder-width
    grip position.
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        super().__init__(config)

    @property
    def exercise_name(self) -> str:
        return "deadlift"

    @property
    def grip_offset_fraction(self) -> float:
        return DEADLIFT_GRIP_FRACTION

    def set_initial_pose(self, robot: ET.Element) -> None:
        """Set starting position: hip-hinged, bar on ground.

        Hips flexed ~80 deg, knees ~60 deg, slight lumbar extension.
        """
        _set_joint_default(robot, "hip", DEADLIFT_HIP_ANGLE)
        _set_joint_default(robot, "knee", DEADLIFT_KNEE_ANGLE)
        _set_joint_default(robot, "lumbar", DEADLIFT_LUMBAR_ANGLE)


def _set_joint_default(robot: ET.Element, prefix: str, value: float) -> None:
    """Set the default position of joints via initial_position attribute."""
    for joint in robot.findall("joint"):
        name = joint.get("name", "")
        if name == prefix or name.startswith(f"{prefix}_"):
            joint.set("initial_position", f"{value:.6f}")


def build_deadlift_model(
    body_mass: float = 80.0,
    height: float = 1.75,
    plate_mass_per_side: float = 80.0,
) -> str:
    """Convenience function to build a deadlift URDF string.

    Default: 80 kg person, 1.75 m tall, 180 kg total barbell.
    """
    from pinocchio_models.shared.barbell import BarbellSpec
    from pinocchio_models.shared.body import BodyModelSpec

    config = ExerciseConfig(
        body_spec=BodyModelSpec(total_mass=body_mass, height=height),
        barbell_spec=BarbellSpec.mens_olympic(plate_mass_per_side=plate_mass_per_side),
    )
    return DeadliftModelBuilder(config).build()
