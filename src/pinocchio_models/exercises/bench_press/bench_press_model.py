"""Bench press model builder (URDF for Pinocchio).

The athlete lies supine on a bench with the barbell held at arms length
above the chest. The barbell is welded to both hands via fixed joints.

Biomechanical notes:
- Primary movers: pectoralis major, anterior deltoid, triceps brachii
- The model captures sagittal-plane pressing kinematics
- Torso is fixed relative to the bench (simplified)

Supine orientation (issue #435): the pelvis hangs from a ``bench`` support
link through a fixed joint pitched -90 degrees about Y, so the chest (+X of the
body frame) points up (+Z) and the head toward -X. With the bench as the
URDF root, Pinocchio's free-flyer moves the bench and the supine lifter
together. Shoulder flexion about -Y swings the arms toward the chest side, so
+90 degrees is "arms straight up" (hands above the shoulders).
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET

from pinocchio_models.exercises.base import ExerciseConfig, ExerciseModelBuilder
from pinocchio_models.shared.constants import (
    BENCH_PRESS_ELBOW_ANGLE,
    BENCH_PRESS_GRIP_FRACTION,
    BENCH_PRESS_HIP_ANGLE,
    BENCH_PRESS_KNEE_ANGLE,
    BENCH_PRESS_SHOULDER_ANGLE,
)
from pinocchio_models.shared.utils.urdf_helpers import (
    add_fixed_joint,
    add_link,
    set_joint_default,
)

# Pitch about Y that lays the lifter supine: body +X (chest) -> world +Z.
_SUPINE_PITCH_RAD: float = -math.pi / 2.0

# The bench is only an orientation/support frame (the bench itself is an
# external constraint), so it carries a negligible mass and inertia.
_BENCH_FRAME_MASS_KG: float = 1e-6
_BENCH_FRAME_INERTIA: float = 1e-9


class BenchPressModelBuilder(ExerciseModelBuilder):
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
    def grip_offset_fraction(self) -> float:
        return BENCH_PRESS_GRIP_FRACTION

    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        """Lay the pelvis supine on a ``bench`` root link, then grip the bar."""
        add_link(
            robot,
            name="bench",
            mass=_BENCH_FRAME_MASS_KG,
            origin_xyz=(0, 0, 0),
            ixx=_BENCH_FRAME_INERTIA,
            iyy=_BENCH_FRAME_INERTIA,
            izz=_BENCH_FRAME_INERTIA,
        )
        add_fixed_joint(
            robot,
            name="pelvis_to_bench",
            parent="bench",
            child="pelvis",
            origin_xyz=(0, 0, 0),
            origin_rpy=(0.0, _SUPINE_PITCH_RAD, 0.0),
        )
        super().attach_barbell(robot, body_links, barbell_links)

    def set_initial_pose(self, robot: ET.Element) -> None:
        """Set lockout position: arms extended above chest.

        Shoulders at 90 deg (arms pointing up), elbows straight,
        hips neutral (supine), knees at 90 deg (feet on floor).

        Note: ``initial_position`` XML attributes are metadata only —
        Pinocchio does not read them at load time.  Use
        ``get_initial_configuration(model, urdf_str)`` from
        ``pinocchio_models.shared.utils.urdf_helpers`` to obtain a
        numpy configuration vector for use with ``pin.forwardKinematics``.
        """
        set_joint_default(
            robot, "shoulder", BENCH_PRESS_SHOULDER_ANGLE, exact_suffix="_flex"
        )
        set_joint_default(robot, "elbow", BENCH_PRESS_ELBOW_ANGLE)
        set_joint_default(robot, "hip", BENCH_PRESS_HIP_ANGLE, exact_suffix="_flex")
        set_joint_default(robot, "knee", BENCH_PRESS_KNEE_ANGLE)


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
