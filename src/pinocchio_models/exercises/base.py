"""Base exercise model builder for Pinocchio (URDF format).

DRY: All exercises share the same skeleton for creating a URDF model --
differing only in barbell attachment strategy and initial pose. This base
class encapsulates the shared workflow; subclasses override hooks to
customize. The barbell lifts take both from the vendored exercise spec
(``spec_lift.SpecLiftBuilder``, LIFT-3).

Law of Demeter: Exercise builders interact with BarbellSpec and BodyModelSpec
through their public APIs, never reaching into internal segment tables.
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pinocchio_models.shared.barbell import BarbellSpec, create_barbell_links
from pinocchio_models.shared.body import BodyModelSpec, create_full_body
from pinocchio_models.shared.contracts.postconditions import ensure_valid_urdf_tree
from pinocchio_models.shared.utils.urdf_helpers import serialize_model

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ExerciseConfig:
    """Immutable configuration common to all exercise models."""

    body_spec: BodyModelSpec = field(default_factory=BodyModelSpec)
    barbell_spec: BarbellSpec = field(default_factory=BarbellSpec.mens_olympic)


class ExerciseModelBuilder(ABC):
    """Abstract builder for exercise-specific Pinocchio URDF models.

    Subclasses must implement:
      - exercise_name: str property
      - attach_barbell(): barbell weld (or bodyweight fixture)
      - set_initial_pose(): default coordinate values for the start position

    Note: Gravity is not set in URDF. It is configured programmatically
    in Pinocchio via model.gravity = pin.Motion(...).
    """

    def __init__(self, config: ExerciseConfig | None = None) -> None:
        """Initialize with an optional exercise configuration.

        Args:
            config: Exercise configuration. Uses default ``ExerciseConfig``
                (50th-percentile male anthropometrics, men's Olympic barbell)
                if ``None``.
        """
        self.config = config or ExerciseConfig()

    @property
    def body_spec(self) -> BodyModelSpec:
        """Law of Demeter: Proxy property for body configuration."""
        return self.config.body_spec

    @property
    def barbell_spec(self) -> BarbellSpec:
        """Law of Demeter: Proxy property for barbell configuration."""
        return self.config.barbell_spec

    @property
    @abstractmethod
    def exercise_name(self) -> str:
        """Human-readable exercise name used in the URDF model."""

    @property
    def uses_barbell(self) -> bool:
        """Whether this exercise uses a barbell.

        Override to ``False`` in bodyweight exercises (gait, sit-to-stand)
        so that ``build()`` skips barbell creation entirely.
        """
        return True

    @abstractmethod
    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        """Attach the barbell (or, for bodyweight exercises, any fixture).

        The barbell lifts (``SpecLiftBuilder``) weld it where the spec start
        via-pose puts it; gait and sit-to-stand add their own fixtures.
        """

    @abstractmethod
    def set_initial_pose(self, robot: ET.Element) -> None:
        """Set default coordinate values for the starting position."""

    def build(self) -> str:
        """Build the complete URDF model XML and return as string.

        Postcondition: returned string is well-formed URDF XML.

        When :attr:`uses_barbell` is ``False`` the barbell links are
        not created and ``attach_barbell`` is still called so that
        subclasses can add alternative fixtures (e.g. a chair for
        sit-to-stand).
        """
        logger.info("Building %s model", self.exercise_name)

        robot = ET.Element("robot", name=self.exercise_name)

        # Build body (pelvis is root link)
        body_links = create_full_body(robot, self.body_spec)

        # Build barbell only when the exercise requires one
        barbell_links: dict[str, ET.Element] = {}
        if self.uses_barbell:
            barbell_links = create_barbell_links(robot, self.barbell_spec)

        # Exercise-specific attachment (or alternative fixture)
        self.attach_barbell(robot, body_links, barbell_links)

        # Exercise-specific initial pose
        self.set_initial_pose(robot)

        # Postcondition: well-formed URDF tree
        # ⚡ Bolt: validate ElementTree in memory directly, skipping redundant XML parsing
        ensure_valid_urdf_tree(robot)

        xml_str = serialize_model(robot)

        logger.info("Built %s model successfully", self.exercise_name)
        return xml_str
