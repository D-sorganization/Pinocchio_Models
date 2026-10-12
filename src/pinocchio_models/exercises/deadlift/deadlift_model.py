"""Deadlift model builder (URDF for Pinocchio).

The athlete grips the barbell with both hands while the bar rests on
the ground. The barbell is welded to both hands via fixed joints.

Biomechanical notes:
- Primary movers: gluteus maximus, hamstrings, erector spinae, quadriceps
- The model captures the hip-hinge pattern in the sagittal plane
- Conventional stance (narrow) is the default
"""

from __future__ import annotations

from pinocchio_models.exercises.base import ExerciseConfig
from pinocchio_models.exercises.spec_lift import SpecLiftBuilder


class DeadliftModelBuilder(SpecLiftBuilder):
    """Builds a deadlift URDF model for Pinocchio.

    The barbell is welded to both hands at the spec grip width; the model
    starts at the spec ``start`` via-pose (setup, loaded bar on the floor).
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        super().__init__(config)

    @property
    def exercise_name(self) -> str:
        return "deadlift"

    @property
    def spec_exercise(self) -> str:
        return "deadlift"


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
