"""Sit-to-stand model builder (URDF for Pinocchio).

Models the transition from seated (on a chair) to standing. A fixed
"chair" body is added to the URDF as an environmental constraint.
No barbell is used.

Biomechanical notes:
- Primary movers: quadriceps, gluteus maximus, hamstrings, erector spinae
- The sit-to-stand movement is divided into 6 phases: seated, weight
  shift, seat-off, momentum transfer, extension, and standing
- Critical for rehabilitation and geriatric assessment
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.base import ExerciseConfig, ExerciseModelBuilder
from pinocchio_models.shared.constants import (
    STS_ANKLE_ANGLE,
    STS_HIP_ANGLE,
    STS_KNEE_ANGLE,
)
from pinocchio_models.shared.utils.urdf_helpers import (
    add_fixed_joint,
    add_link,
    set_joint_default,
)

# Chair seat height in meters (standard chair height ~0.45 m)
_CHAIR_SEAT_HEIGHT_M: float = 0.45

# Chair seat depth (front-to-back) in meters
_CHAIR_SEAT_DEPTH_M: float = 0.40


class SitToStandModelBuilder(ExerciseModelBuilder):
    """Builds a sit-to-stand URDF model for Pinocchio.

    Adds a fixed chair body to the environment and sets the initial
    pose to a seated position. No barbell is attached.
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        super().__init__(config)

    @property
    def exercise_name(self) -> str:
        return "sit_to_stand"

    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        """No barbell for sit-to-stand — add chair body instead."""
        # Add a chair seat as a fixed environmental body
        add_link(
            robot,
            name="chair_seat",
            mass=5.0,
            origin_xyz=(0, 0, 0),
            ixx=0.01,
            iyy=0.01,
            izz=0.01,
        )
        # Attach chair to the world via a fixed joint at seat height
        # The chair is positioned behind and below the pelvis
        add_fixed_joint(
            robot,
            name="chair_to_world",
            parent="pelvis",
            child="chair_seat",
            origin_xyz=(-_CHAIR_SEAT_DEPTH_M / 2, 0, -_CHAIR_SEAT_HEIGHT_M),
        )

    def set_initial_pose(self, robot: ET.Element) -> None:
        """Set seated initial pose.

        Hips and knees flexed to approximately 90 degrees,
        representing a person seated on a standard-height chair.
        """
        set_joint_default(robot, "hip", STS_HIP_ANGLE, exact_suffix="_flex")
        set_joint_default(robot, "knee", STS_KNEE_ANGLE)
        set_joint_default(robot, "ankle", STS_ANKLE_ANGLE, exact_suffix="_flex")


def build_sit_to_stand_model(
    body_mass: float = 70.0,
    height: float = 1.75,
    plate_mass_per_side: float = 0.0,
) -> str:
    """Convenience function to build a sit-to-stand model URDF string.

    Default: 70 kg person, 1.75 m tall, no external load.
    The plate_mass_per_side parameter is accepted for CLI compatibility
    but ignored (sit-to-stand has no barbell).
    """
    from pinocchio_models.shared.barbell import BarbellSpec
    from pinocchio_models.shared.body import BodyModelSpec

    config = ExerciseConfig(
        body_spec=BodyModelSpec(total_mass=body_mass, height=height),
        barbell_spec=BarbellSpec.mens_olympic(plate_mass_per_side=0.0),
    )
    return SitToStandModelBuilder(config).build()
