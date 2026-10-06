"""Real-engine kinematic probes for the parity fingerprint.

Measures, with Pinocchio forward kinematics, what the parity standard's
``kinematics`` block specifies: each coordinate's rotation axis (relative to
the pelvis, at the all-zero pose), the pelvis's world rotation, and every human
segment's origin at the standard test poses. Raw values are in engine frame and
keyed by Pinocchio names; ``assemble.assemble_fingerprint`` maps and rebases
them onto the canonical frame.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

from pinocchio_models.shared.parity._canonical import kinematics, topology

Vec3 = tuple[float, float, float]
_PELVIS = "pelvis"


def _frames(model: Any, q: Any) -> Any:
    """Return pinocchio ``data`` with frame placements for configuration *q*."""
    import pinocchio as pin

    data = model.createData()
    pin.framesForwardKinematics(model, data, q)
    return data


def _rotation(model: Any, data: Any, body: str) -> list[list[float]]:
    """World rotation (3x3 rows) of the body frame called *body*."""
    rot = data.oMf[model.getFrameId(body)].rotation
    return [[float(v) for v in row] for row in rot]


def _origin(model: Any, data: Any, body: str) -> Vec3:
    pos = data.oMf[model.getFrameId(body)].translation
    return (float(pos[0]), float(pos[1]), float(pos[2]))


def _with_coordinates(
    model: Any, values: Mapping[str, float], names: Mapping[str, str]
) -> Any:
    """Neutral configuration with the canonical coordinates in *values* set."""
    import pinocchio as pin

    q = pin.neutral(model)
    for coord, angle in values.items():
        joint = model.joints[model.getJointId(names.get(coord, coord))]
        q[joint.idx_q] = angle
    return q


def pelvis_rotation(model: Any) -> list[Vec3]:
    """The pelvis frame's world rotation at the neutral pose (rows)."""
    import pinocchio as pin

    data = _frames(model, pin.neutral(model))
    return [(r[0], r[1], r[2]) for r in _rotation(model, data, _PELVIS)]


def _probe_axis(
    model: Any, coord: str, segment: str, angle: float, names: Mapping[str, str]
) -> Vec3:
    before = _frames(model, _with_coordinates(model, {}, names))
    after = _frames(model, _with_coordinates(model, {coord: angle}, names))
    return kinematics.segment_axis(
        _rotation(model, before, _PELVIS),
        _rotation(model, before, segment),
        _rotation(model, after, _PELVIS),
        _rotation(model, after, segment),
    )


def coordinate_axes(
    model: Any, std: dict[str, Any], aliases: Mapping[str, str]
) -> dict[str, Vec3]:
    """Measured axis of every standard coordinate, keyed by engine joint name."""
    names = {canon: eng for eng, canon in aliases.items()}
    angle = kinematics.probe_angle_rad(std)
    return {
        names.get(coord, coord): _probe_axis(model, coord, seg, angle, names)
        for coord, seg in kinematics.axis_probes(std).items()
    }


def _pose_origins(
    model: Any, std: dict[str, Any], q: Mapping[str, float], names: Mapping[str, str]
) -> dict[str, Vec3]:
    data = _frames(model, _with_coordinates(model, q, names))
    return {seg: _origin(model, data, seg) for seg in _human_segments(std)}


def _human_segments(std: dict[str, Any]) -> list[str]:
    return sorted(set(kinematics.axis_probes(std).values()) | {_PELVIS})


def pose_origins(
    model: Any, std: dict[str, Any], aliases: Mapping[str, str]
) -> dict[str, dict[str, Vec3]]:
    """Every human segment's world origin at each standard test pose."""
    names = {canon: eng for eng, canon in aliases.items()}
    return {
        pose: _pose_origins(model, std, q, names)
        for pose, q in topology.standard_poses(std).items()
    }
