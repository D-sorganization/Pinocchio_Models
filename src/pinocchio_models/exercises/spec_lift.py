"""Barbell lifts that start at the spec ``start`` via-pose (LIFT-3).

UpstreamDrift#11743: the start pose of every barbell lift is the vendored
exercise spec's ``start`` via-pose (``_canonical/biomech_parity_standard.json``,
standard v2.1), never a pack-local literal: every joint coordinate (unlisted
ones are 0), the pelvis root placement and the bar centre. Because this
model's kinematics *is* the standard's (``canonical_topology`` reads axes and
joint origins from it), the standard's own reference forward kinematics
(``_canonical/topology``) gives the segment frames of that pose, and the bar
weld is the bar's placement in the holding segment's frame. The engine
reproduces the pose exactly; ``tests/parity/test_spec_start_pose.py`` checks
it in real Pinocchio.

Positions in the spec are for the standard lifter height and scale linearly
with height (``pose_frame``); joint angles do not scale.

Design by Contract:
    - Preconditions: the exercise has a ``start`` via-pose; height > 0; the
      bar is placed in a human segment of the standard. Violations raise
      ValueError.
    - Postconditions: the bar is level (world-aligned, axis along canonical
      +Y) at the spec bar position, both palm centres on it at the spec grip
      width; ``coordinates()`` names every model coordinate.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from abc import abstractmethod
from dataclasses import dataclass
from typing import Any

from pinocchio_models.exercises.base import ExerciseModelBuilder
from pinocchio_models.shared.parity._canonical import conformance, spec, topology
from pinocchio_models.shared.parity.fingerprint import COORDINATE_ALIASES
from pinocchio_models.shared.utils.geometry import rpy_from_matrix
from pinocchio_models.shared.utils.urdf_helpers import (
    add_fixed_joint,
    add_link,
    set_joint_default,
    set_root_default,
)

STANDARD: dict[str, Any] = conformance.load_standard()

# Canonical coordinate -> this model's joint name (only names that differ).
_ENGINE_NAME: dict[str, str] = {c: e for e, c in COORDINATE_ALIASES.items()}

# The right grip is a zero-mass marker on the shaft (URDF allows one parent).
_MARKER_MASS_KG: float = 1e-6
_MARKER_INERTIA: float = 1e-9

Vec3 = tuple[float, float, float]
Placement = tuple[Vec3, Vec3]


@dataclass(frozen=True)
class SpecStart:
    """The spec ``start`` via-pose of one lift, for a lifter of *height* m."""

    exercise: str
    height: float

    def __post_init__(self) -> None:
        if not self.height > 0.0:
            raise ValueError(f"height must be positive, got {self.height}")
        # Raises ValueError for an unknown exercise or one without a start.
        spec.pose_coordinates(STANDARD, self.exercise, "start")

    @property
    def _pose(self) -> dict[str, Any]:
        poses: dict[str, Any] = spec.exercise_spec(STANDARD, self.exercise)
        return dict(poses["via_poses"]["start"])

    @property
    def _scale(self) -> float:
        return self.height / float(STANDARD["anthropometrics"]["height_m"])

    def _scaled(self, vec: Any) -> Vec3:
        x, y, z = (float(v) * self._scale for v in vec)
        return (x, y, z)

    def coordinates(self) -> dict[str, float]:
        """Joint angle (rad) of every model coordinate, keyed by joint name."""
        out = dict.fromkeys(conformance.expected_coordinates(STANDARD), 0.0)
        out.update(spec.pose_coordinates(STANDARD, self.exercise, "start"))
        return {_ENGINE_NAME.get(name, name): value for name, value in out.items()}

    def root(self) -> Placement:
        """Pelvis placement in the world: position (m), URDF rpy (rad)."""
        root = self._pose["root"]
        roll, pitch, yaw = (float(v) for v in root["orientation_rpy_rad"])
        return self._scaled(root["position_m"]), (roll, pitch, yaw)

    @property
    def grip_half_width_m(self) -> float:
        """Half the spec grip width: palm centre to bar centre along the bar."""
        grip = spec.exercise_spec(STANDARD, self.exercise)["grip"]
        return float(grip["width_m"]) / 2.0 * self._scale

    def bar_in(self, segment: str) -> Placement:
        """Placement of the level bar centre in *segment*'s frame at the start.

        Raises:
            ValueError: *segment* is not a human segment of the standard.
        """
        root = self._pose["root"]
        frames = topology.world_frames(
            STANDARD,
            spec.pose_coordinates(STANDARD, self.exercise, "start"),
            root["position_m"],
            root["orientation_rpy_rad"],
        )
        if segment not in frames:
            raise ValueError(f"unknown segment {segment!r}; known: {sorted(frames)}")
        origin, rot = frames[segment]
        inverse = [[rot[j][i] for j in range(3)] for i in range(3)]
        bar = self._pose["bar_position_m"]
        offset = [float(b) - float(o) for b, o in zip(bar, origin, strict=True)]
        return self._scaled(topology.rotate(inverse, offset)), rpy_from_matrix(inverse)


class SpecLiftBuilder(ExerciseModelBuilder):
    """A barbell lift whose start pose and bar placement come from the spec.

    The default barbell attachment welds the shaft to ``hand_l`` where the
    spec start puts it and hangs the right grip marker at the spec grip
    width; the squat overrides it to weld the bar to the torso. Bench press
    sets ``free_root`` to False because its pelvis is placed by the bench
    weld instead of the free-flyer.
    """

    @property
    @abstractmethod
    def spec_exercise(self) -> str:
        """Exercise id of this lift in the parity standard (e.g. ``squat``)."""

    @property
    def free_root(self) -> bool:
        """Whether the free-flyer carries the start root placement."""
        return True

    @property
    def spec_start(self) -> SpecStart:
        """The spec start via-pose scaled to this lifter's height."""
        return SpecStart(self.spec_exercise, self.body_spec.height)

    def attach_barbell(
        self,
        robot: ET.Element,
        body_links: dict[str, ET.Element],
        barbell_links: dict[str, ET.Element],
    ) -> None:
        """Weld the shaft to ``hand_l`` at the spec start; mark the right grip."""
        xyz, rpy = self.spec_start.bar_in("hand_l")
        add_fixed_joint(
            robot,
            name="barbell_to_hand_l",
            parent="hand_l",
            child="barbell_shaft",
            origin_xyz=xyz,
            origin_rpy=rpy,
        )
        add_link(
            robot,
            name="barbell_grip_r",
            mass=_MARKER_MASS_KG,
            origin_xyz=(0, 0, 0),
            ixx=_MARKER_INERTIA,
            iyy=_MARKER_INERTIA,
            izz=_MARKER_INERTIA,
        )
        add_fixed_joint(
            robot,
            name="barbell_to_hand_r",
            parent="barbell_shaft",
            child="barbell_grip_r",
            origin_xyz=(0, -self.spec_start.grip_half_width_m, 0),
        )

    def set_initial_pose(self, robot: ET.Element) -> None:
        """Stamp the spec start coordinates (and root) as initial metadata.

        ``initial_position`` / root attributes are metadata only; use
        ``get_initial_configuration(model, urdf_str)`` from
        ``pinocchio_models.shared.utils.urdf_helpers`` to obtain the
        configuration vector.
        """
        start = self.spec_start
        for joint, value in start.coordinates().items():
            set_joint_default(robot, joint, value)
        if self.free_root:
            set_root_default(robot, *start.root())
