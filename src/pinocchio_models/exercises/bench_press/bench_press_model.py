"""Bench press model builder (URDF for Pinocchio).

The athlete lies supine on a bench with the barbell held at arms length
above the chest. The barbell is welded to both hands via fixed joints.

Biomechanical notes:
- Primary movers: pectoralis major, anterior deltoid, triceps brachii
- The model captures sagittal-plane pressing kinematics
- Torso is fixed relative to the bench (simplified)

Supine placement (issue #435, #466): the pelvis hangs from a ``bench``
support link through a fixed joint at the spec ``start`` via-pose root
(position and pitch -pi/2, so the chest (+X of the body frame) points up
(+Z) and the head toward -X). With the bench as the URDF root at the world
origin, the model conforms to standard v2.0's ``root_joint: weld``
(Universe -> bench fixed base). The model starts at the spec ``unrack`` via-pose.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.base import ExerciseConfig
from pinocchio_models.exercises.spec_lift import SpecLiftBuilder
from pinocchio_models.shared.utils.urdf_helpers import add_fixed_joint, add_link

# The bench is only an orientation/support frame (the bench itself is an
# external constraint), so it carries a negligible mass and inertia.
_BENCH_FRAME_MASS_KG: float = 1e-6
_BENCH_FRAME_INERTIA: float = 1e-9


class BenchPressModelBuilder(SpecLiftBuilder):
    """Builds a bench press URDF model for Pinocchio.

    The barbell is welded to both hands. The torso is assumed to be
    supported by the bench (constraint applied externally).
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        super().__init__(config)

    @property
    def exercise_name(self) -> str:
        return "bench_press"

    @property
    def spec_exercise(self) -> str:
        return "bench_press"

    @property
    def free_root(self) -> bool:
        """The bench weld, not the free-flyer, places the supine pelvis."""
        return False

    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        """Weld the pelvis to a ``bench`` root at the spec root, then grip."""
        add_link(
            robot,
            name="bench",
            mass=_BENCH_FRAME_MASS_KG,
            origin_xyz=(0, 0, 0),
            ixx=_BENCH_FRAME_INERTIA,
            iyy=_BENCH_FRAME_INERTIA,
            izz=_BENCH_FRAME_INERTIA,
        )
        xyz, rpy = self.spec_start.root()
        add_fixed_joint(
            robot,
            name="pelvis_to_bench",
            parent="bench",
            child="pelvis",
            origin_xyz=xyz,
            origin_rpy=rpy,
        )
        super().attach_barbell(robot, body_links, barbell_links)


def build_bench_press_model(
    body_mass: float = 80.0,
    height: float = 1.75,
    plate_mass_per_side: float = 50.0,
) -> str:
    """Convenience function to build a bench press URDF string.

    Default: 80 kg person, 1.75 m tall, 120 kg total barbell.
    """
    from pinocchio_models.shared.barbell import BarbellSpec
    from pinocchio_models.shared.body import BodyModelSpec

    config = ExerciseConfig(
        body_spec=BodyModelSpec(total_mass=body_mass, height=height),
        barbell_spec=BarbellSpec.mens_olympic(plate_mass_per_side=plate_mass_per_side),
    )
    return BenchPressModelBuilder(config).build()
