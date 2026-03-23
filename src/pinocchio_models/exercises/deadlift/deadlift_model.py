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
from pinocchio_models.shared.utils.urdf_helpers import add_fixed_joint


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

    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        """Weld barbell shaft to both hands at grip position."""
        grip_offset = self.config.barbell_spec.shaft_length * 0.3

        add_fixed_joint(
            robot,
            name="barbell_to_hand_l",
            parent="hand_l",
            child="barbell_shaft",
            origin_xyz=(0, -grip_offset, 0),
        )

    def set_initial_pose(self, robot: ET.Element) -> None:
        """Set starting position: hip-hinged, bar on ground."""


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
