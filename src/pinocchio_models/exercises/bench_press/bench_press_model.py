"""Bench press model builder (URDF for Pinocchio).

The athlete lies supine on a bench with the barbell held at arms length
above the chest. The barbell is welded to both hands via fixed joints.

Biomechanical notes:
- Primary movers: pectoralis major, anterior deltoid, triceps brachii
- The model captures sagittal-plane pressing kinematics
- Torso is fixed relative to the bench (simplified)
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pinocchio_models.exercises.base import ExerciseConfig, ExerciseModelBuilder
from pinocchio_models.shared.constants import (
    BENCH_PRESS_ELBOW_ANGLE,
    BENCH_PRESS_GRIP_FRACTION,
    BENCH_PRESS_HIP_ANGLE,
    BENCH_PRESS_KNEE_ANGLE,
    BENCH_PRESS_SHOULDER_ANGLE,
)


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

    def set_initial_pose(self, robot: ET.Element) -> None:
        """Set lockout position: arms extended above chest.

        Shoulders at 90 deg (arms pointing up), elbows straight,
        hips neutral (supine), knees at 90 deg (feet on floor).
        """
        _set_joint_default(robot, "shoulder", BENCH_PRESS_SHOULDER_ANGLE)
        _set_joint_default(robot, "elbow", BENCH_PRESS_ELBOW_ANGLE)
        _set_joint_default(robot, "hip", BENCH_PRESS_HIP_ANGLE)
        _set_joint_default(robot, "knee", BENCH_PRESS_KNEE_ANGLE)


def _set_joint_default(robot: ET.Element, prefix: str, value: float) -> None:
    """Set the default position of bilateral joints via URDF comments.

    Stores initial pose as an XML comment for downstream consumers.
    Pinocchio does not read default joint values from URDF, but this
    documents the intended starting configuration.
    """
    for side in ("l", "r"):
        joint_name = f"{prefix}_{side}"
        for joint in robot.findall("joint"):
            if joint.get("name") == joint_name:
                joint.set("initial_position", f"{value:.6f}")


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
