"""Snatch model builder (URDF for Pinocchio).

The snatch is a single continuous movement lifting the barbell from
the ground to overhead in one motion. The barbell is gripped with a
wide (snatch) grip and welded to the hands.

Biomechanical notes:
- Primary movers: full posterior chain, deltoids, trapezius
- Three phases: first pull, second pull (triple extension), overhead squat
- Wide grip reduces the vertical distance the bar must travel
"""

from __future__ import annotations

from pinocchio_models.exercises.base import ExerciseConfig
from pinocchio_models.exercises.spec_lift import SpecLiftBuilder


class SnatchModelBuilder(SpecLiftBuilder):
    """Builds a snatch URDF model for Pinocchio.

    The barbell is welded to both hands at the spec's wide (snatch) grip
    width; the model starts at the spec ``start`` via-pose (setup, loaded bar
    on the floor).
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        super().__init__(config)

    @property
    def exercise_name(self) -> str:
        return "snatch"

    @property
    def spec_exercise(self) -> str:
        return "snatch"


def build_snatch_model(
    body_mass: float = 80.0,
    height: float = 1.75,
    plate_mass_per_side: float = 40.0,
) -> str:
    """Convenience function to build a snatch URDF string.

    Default: 80 kg person, 1.75 m tall, 100 kg total barbell.
    """
    from pinocchio_models.shared.barbell import BarbellSpec
    from pinocchio_models.shared.body import BodyModelSpec

    config = ExerciseConfig(
        body_spec=BodyModelSpec(total_mass=body_mass, height=height),
        barbell_spec=BarbellSpec.mens_olympic(plate_mass_per_side=plate_mass_per_side),
    )
    return SnatchModelBuilder(config).build()
