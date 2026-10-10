"""Base exercise model builder for Pinocchio (URDF format).

DRY: All five exercises share the same skeleton for creating a URDF
model -- differing only in barbell attachment strategy, initial pose,
and joint coordinate defaults. This base class encapsulates the shared
workflow; subclasses override hooks to customize.

Law of Demeter: Exercise builders interact with BarbellSpec and BodyModelSpec
through their public APIs, never reaching into internal segment tables.
"""

from __future__ import annotations

import logging
import math
import xml.etree.ElementTree as ET
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

from pinocchio_models.shared.barbell import BarbellSpec, create_barbell_links
from pinocchio_models.shared.body import BodyModelSpec, create_full_body
from pinocchio_models.shared.body.canonical_topology import solve_grip_abduction
from pinocchio_models.shared.contracts.postconditions import ensure_valid_urdf_tree
from pinocchio_models.shared.utils.urdf_helpers import (
    add_fixed_joint,
    add_link,
    add_virtual_link,
    serialize_model,
)

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
      - grip_offset_fraction: float property (fraction of shaft length)
      - set_initial_pose(): default coordinate values for the start position

    The base class provides a default ``attach_barbell()`` that welds the
    barbell shaft to both hands via fixed joints. Override for exercises
    that attach the barbell differently (e.g., squat attaches to torso).

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

    @property
    def grip_offset_fraction(self) -> float:
        """Fraction of shaft_length from center to each grip point.

        Override in subclasses to customize grip width. Default is 0.3
        (shoulder-width). Snatch uses ~0.45 (wide grip).
        """
        return 0.3

    @property
    def upper_body_tilt_rad(self) -> float:
        """Net rotation about the shared Y axis, upstream of the grip joint.

        Lumbar and shoulder flexion (and, for bench press, the supine pitch)
        rotate the torso/arm chain about the world Y axis. That rotation
        never moves the hand's lateral (grip) position -- see
        :func:`~pinocchio_models.shared.body.canonical_topology.solve_grip_abduction`
        -- but it does rotate the hand's frame, so the barbell weld must
        cancel it to keep the bar level (issue #443). Zero by default;
        override in subclasses whose ``set_initial_pose`` sets a nonzero
        lumbar or shoulder flexion angle.
        """
        return 0.0

    @property
    def _grip_offset_m(self) -> float:
        """Distance from the barbell shaft centre to each grip point."""
        return self.barbell_spec.shaft_length * self.grip_offset_fraction

    @property
    def _grip_abduction_rad(self) -> float:
        """Shoulder-adduction angle placing each hand at ``_grip_offset_m``."""
        return solve_grip_abduction(self._grip_offset_m, self.body_spec.height)

    @staticmethod
    def _attach_shaft_to_left_hand(
        robot: ET.Element,
        grip_offset: float,
        abduction_rad: float = 0.0,
        tilt_rad: float = 0.0,
    ) -> None:
        """Weld ``barbell_shaft`` to ``hand_l`` and level it to the world frame.

        The left hand's own orientation is rotated away from the world frame
        by the pose's shoulder-abduction angle (``abduction_rad``, about the
        mirrored local X axis) and any upstream lumbar/shoulder flexion
        (``tilt_rad``, about the shared Y axis). A virtual link inverts
        exactly those two rotations -- roll by ``abduction_rad``, then pitch
        by ``-tilt_rad`` -- so the shaft ends up level (world-aligned) with
        its centre offset from ``hand_l`` by a pure world-Y vector of length
        ``grip_offset`` (issue #443). With both angles zero this reduces to
        the previous single fixed-offset weld.

        URDF requires each link to have exactly one parent joint; attaching
        barbell_shaft to hand_l only (and mirroring the right-hand grip via
        a virtual link) keeps the topology a valid tree.
        """
        add_virtual_link(robot, name="barbell_hand_l_pivot")
        add_fixed_joint(
            robot,
            name="barbell_to_hand_l",
            parent="hand_l",
            child="barbell_hand_l_pivot",
            origin_xyz=(
                0.0,
                -grip_offset * math.cos(abduction_rad),
                -grip_offset * math.sin(abduction_rad),
            ),
            origin_rpy=(abduction_rad, 0.0, 0.0),
        )
        add_fixed_joint(
            robot,
            name="barbell_hand_l_pivot_to_shaft",
            parent="barbell_hand_l_pivot",
            child="barbell_shaft",
            origin_rpy=(0.0, -tilt_rad, 0.0),
        )

    @staticmethod
    def _attach_virtual_grip_right(robot: ET.Element, grip_offset: float) -> None:
        """Create the zero-mass ``barbell_grip_r`` anchor and fix it to the shaft.

        hand_r already has ``wrist_r`` as its URDF parent, so adding a second
        parent would be invalid.  We hang ``barbell_grip_r`` off
        ``barbell_shaft`` at the right grip position (-``grip_offset``, the
        right hand being at -Y), producing the valid
        tree ``hand_l -> barbell_shaft -> barbell_grip_r``.
        """
        add_link(
            robot,
            name="barbell_grip_r",
            mass=1e-6,
            origin_xyz=(0, 0, 0),
            ixx=1e-9,
            iyy=1e-9,
            izz=1e-9,
        )
        add_fixed_joint(
            robot,
            name="barbell_to_hand_r",
            parent="barbell_shaft",
            child="barbell_grip_r",
            origin_xyz=(0, -grip_offset, 0),
        )

    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        """Weld barbell shaft to both hands at grip position.

        DRY: This default implementation covers bench press, deadlift,
        snatch, and clean-and-jerk. The squat overrides this entirely
        because the barbell sits on the torso, not in the hands.
        """
        grip_offset = self._grip_offset_m
        self._attach_shaft_to_left_hand(
            robot, grip_offset, self._grip_abduction_rad, self.upper_body_tilt_rad
        )
        self._attach_virtual_grip_right(robot, grip_offset)

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
