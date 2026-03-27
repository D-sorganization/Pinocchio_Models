"""Back squat model builder (URDF for Pinocchio).

The barbell rests across the upper trapezius / rear deltoids (high-bar
position) and is rigidly welded to the torso at shoulder height. The
initial pose places the model in a standing position with neutral
joint angles (the "unrack" position).

Biomechanical notes:
- Primary movers: quadriceps, gluteus maximus, hamstrings, erector spinae
- The model captures sagittal-plane kinematics (flexion/extension)
- Barbell path should remain roughly over mid-foot
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.base import ExerciseConfig, ExerciseModelBuilder
from pinocchio_models.shared.constants import (
    SQUAT_ANKLE_ANGLE,
    SQUAT_HIP_ANGLE,
    SQUAT_KNEE_ANGLE,
)
from pinocchio_models.shared.utils.urdf_helpers import (
    add_fixed_joint,
    set_joint_default,
)

# Vertical offset (m) from the top of the torso to the trap-bar attachment point.
# Represents the approximate distance from the top of the trapezius to the
# barbell resting position in a high-bar back squat.
_TRAP_BAR_OFFSET_M: float = 0.03


class SquatModelBuilder(ExerciseModelBuilder):
    """Builds a back-squat URDF model for Pinocchio.

    The barbell is welded to the torso at the approximate position of the
    upper trapezius (high-bar squat). Overrides the default attach_barbell
    since the squat does not use hand grip attachment.
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        super().__init__(config)

    @property
    def exercise_name(self) -> str:
        return "back_squat"

    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        """Weld barbell shaft to torso at upper trap position (Z-up)."""
        torso_len = self.config.body_spec.height * 0.288
        trap_height = torso_len - _TRAP_BAR_OFFSET_M

        add_fixed_joint(
            robot,
            name="barbell_to_torso",
            parent="torso",
            child="barbell_shaft",
            origin_xyz=(0, 0, trap_height),
        )

    def set_initial_pose(self, robot: ET.Element) -> None:
        """Set standing unrack position: neutral joint angles.

        All leg joints at neutral (standing straight).

        Note: ``initial_position`` XML attributes are metadata only —
        Pinocchio does not read them at load time.  Use
        ``get_initial_configuration(model, urdf_str)`` from
        ``pinocchio_models.shared.utils.urdf_helpers`` to obtain a
        numpy configuration vector for use with ``pin.forwardKinematics``.
        """
        set_joint_default(robot, "hip", SQUAT_HIP_ANGLE, exact_suffix="_flex")
        set_joint_default(robot, "knee", SQUAT_KNEE_ANGLE)
        set_joint_default(robot, "ankle", SQUAT_ANKLE_ANGLE, exact_suffix="_flex")


def build_squat_model(
    body_mass: float = 80.0,
    height: float = 1.75,
    plate_mass_per_side: float = 60.0,
) -> str:
    """Convenience function to build a squat model URDF string.

    Default: 80 kg person, 1.75 m tall, 140 kg total barbell
    (20 kg bar + 60 kg per side).
    """
    from pinocchio_models.shared.barbell import BarbellSpec
    from pinocchio_models.shared.body import BodyModelSpec

    config = ExerciseConfig(
        body_spec=BodyModelSpec(total_mass=body_mass, height=height),
        barbell_spec=BarbellSpec.mens_olympic(plate_mass_per_side=plate_mass_per_side),
    )
    return SquatModelBuilder(config).build()
