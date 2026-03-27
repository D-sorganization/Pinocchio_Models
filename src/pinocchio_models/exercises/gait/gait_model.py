"""Gait (walking) model builder (URDF for Pinocchio).

No barbell — the model represents unloaded bipedal walking. The initial
pose places the model in a natural standing position with slight knee
flexion (mid-stance ready).

Biomechanical notes:
- Primary movers: hip flexors/extensors, quadriceps, hamstrings,
  gastrocnemius/soleus, tibialis anterior
- The gait cycle is divided into 8 phases from heel strike through
  swing to the next heel strike
- Balance mode is alternating single-leg stance
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.base import ExerciseConfig, ExerciseModelBuilder
from pinocchio_models.shared.constants import (
    GAIT_ANKLE_ANGLE,
    GAIT_HIP_ANGLE,
    GAIT_KNEE_ANGLE,
)
from pinocchio_models.shared.utils.urdf_helpers import set_joint_default


class GaitModelBuilder(ExerciseModelBuilder):
    """Builds a bipedal walking URDF model for Pinocchio.

    No barbell is attached — this is an unloaded gait model. The
    ``attach_barbell`` method is overridden to be a no-op, and the
    ``build`` method is overridden to skip barbell creation entirely.
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        super().__init__(config)

    @property
    def exercise_name(self) -> str:
        return "gait"

    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        """No barbell for gait — intentional no-op."""

    def set_initial_pose(self, robot: ET.Element) -> None:
        """Set natural standing pose with slight knee flexion.

        Represents the mid-stance ready position before the first
        heel strike.
        """
        set_joint_default(robot, "hip", GAIT_HIP_ANGLE, exact_suffix="_flex")
        set_joint_default(robot, "knee", GAIT_KNEE_ANGLE)
        set_joint_default(robot, "ankle", GAIT_ANKLE_ANGLE, exact_suffix="_flex")


def build_gait_model(
    body_mass: float = 70.0,
    height: float = 1.75,
    plate_mass_per_side: float = 0.0,
) -> str:
    """Convenience function to build a gait model URDF string.

    Default: 70 kg person, 1.75 m tall, no external load.
    The plate_mass_per_side parameter is accepted for CLI compatibility
    but ignored (gait has no barbell).
    """
    from pinocchio_models.shared.barbell import BarbellSpec
    from pinocchio_models.shared.body import BodyModelSpec

    config = ExerciseConfig(
        body_spec=BodyModelSpec(total_mass=body_mass, height=height),
        barbell_spec=BarbellSpec.mens_olympic(plate_mass_per_side=0.0),
    )
    return GaitModelBuilder(config).build()
