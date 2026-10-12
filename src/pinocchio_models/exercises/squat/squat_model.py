"""Back squat model builder (URDF for Pinocchio).

The barbell rests across the upper back and is rigidly welded to the torso
where the spec ``start`` via-pose puts it; the model starts at that via-pose
(standing unrack, LIFT-3, UpstreamDrift#11743), with both hands on the bar.

Biomechanical notes:
- Primary movers: quadriceps, gluteus maximus, hamstrings, erector spinae
- Barbell path should remain roughly over mid-foot
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.base import ExerciseConfig
from pinocchio_models.exercises.spec_lift import SpecLiftBuilder
from pinocchio_models.shared.utils.urdf_helpers import add_fixed_joint


class SquatModelBuilder(SpecLiftBuilder):
    """Builds a back-squat URDF model for Pinocchio.

    The barbell is welded to the torso at its spec start position. Overrides
    the default attach_barbell since the bar rests on the back, not in the
    hands.
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        super().__init__(config)

    @property
    def exercise_name(self) -> str:
        return "back_squat"

    @property
    def spec_exercise(self) -> str:
        return "squat"

    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        """Weld barbell shaft to the torso at the spec start bar position."""
        xyz, rpy = self.spec_start.bar_in("torso")
        add_fixed_joint(
            robot,
            name="barbell_to_torso",
            parent="torso",
            child="barbell_shaft",
            origin_xyz=xyz,
            origin_rpy=rpy,
        )


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
