"""Base exercise model builder for Pinocchio (URDF format).

DRY: All five exercises share the same skeleton for creating a URDF
model — differing only in barbell attachment strategy, initial pose,
and joint coordinate defaults. This base class encapsulates the shared
workflow; subclasses override hooks to customize.

Law of Demeter: Exercise builders interact with BarbellSpec and BodyModelSpec
through their public APIs, never reaching into internal segment tables.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pinocchio_models.shared.barbell import BarbellSpec, create_barbell_links
from pinocchio_models.shared.body import BodyModelSpec, create_full_body
from pinocchio_models.shared.contracts.postconditions import ensure_valid_urdf
from pinocchio_models.shared.utils.urdf_helpers import serialize_model


@dataclass
class ExerciseConfig:
    """Configuration common to all exercise models."""

    body_spec: BodyModelSpec = field(default_factory=BodyModelSpec)
    barbell_spec: BarbellSpec = field(default_factory=BarbellSpec.mens_olympic)


class ExerciseModelBuilder(ABC):
    """Abstract builder for exercise-specific Pinocchio URDF models.

    Subclasses must implement:
      - exercise_name: str property
      - attach_barbell(): how the barbell connects to the body
      - set_initial_pose(): default coordinate values for the start position

    Note: Gravity is not set in URDF. It is configured programmatically
    in Pinocchio via model.gravity = pin.Motion(...).
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        self.config = config or ExerciseConfig()

    @property
    @abstractmethod
    def exercise_name(self) -> str:
        """Human-readable exercise name used in the URDF model."""

    @abstractmethod
    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        """Add joints connecting barbell to body (exercise-specific)."""

    @abstractmethod
    def set_initial_pose(self, robot: ET.Element) -> None:
        """Set default coordinate values for the starting position."""

    def build(self) -> str:
        """Build the complete URDF model XML and return as string.

        Postcondition: returned string is well-formed URDF XML.
        """
        robot = ET.Element("robot", name=self.exercise_name)

        # Build body (pelvis is root link)
        body_links = create_full_body(robot, self.config.body_spec)

        # Build barbell
        barbell_links = create_barbell_links(robot, self.config.barbell_spec)

        # Exercise-specific attachment
        self.attach_barbell(robot, body_links, barbell_links)

        # Exercise-specific initial pose
        self.set_initial_pose(robot)

        xml_str = serialize_model(robot)

        # Postcondition: well-formed URDF
        ensure_valid_urdf(xml_str)

        return xml_str
