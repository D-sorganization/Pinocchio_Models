"""Engine-free URDF checks: canonical axes and sides (issue #435).

Every joint frame is aligned with the world at q=0, so the ``<axis>`` literal
of each coordinate equals the canonical axis of the parity standard and left
segments sit at +Y, right at -Y.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models.exercises.squat.squat_model import build_squat_model
from pinocchio_models.shared.parity._canonical import conformance, kinematics
from pinocchio_models.shared.parity.fingerprint import COORDINATE_ALIASES

STD = conformance.load_standard()
_ENGINE_NAME = {canon: eng for eng, canon in COORDINATE_ALIASES.items()}


@pytest.fixture(scope="module")
def joints() -> dict[str, ET.Element]:
    root = ET.fromstring(build_squat_model())
    return {j.get("name", ""): j for j in root.findall("joint")}


def _vec(text: str) -> tuple[float, ...]:
    return tuple(float(v) for v in text.split())


@pytest.mark.parametrize("coord, axis", sorted(kinematics.expected_axes(STD).items()))
def test_joint_axis_literal_is_canonical(
    joints: dict[str, ET.Element], coord: str, axis: tuple[float, ...]
) -> None:
    joint = joints[_ENGINE_NAME.get(coord, coord)]
    assert _vec(joint.find("axis").get("xyz", "")) == pytest.approx(axis)  # type: ignore[union-attr]


def test_joint_frames_are_not_rotated(joints: dict[str, ET.Element]) -> None:
    for name, joint in joints.items():
        rpy = joint.find("origin").get("rpy", "0 0 0")  # type: ignore[union-attr]
        if name == "pelvis_to_bench":
            continue
        assert _vec(rpy) == (0.0, 0.0, 0.0), name


@pytest.mark.parametrize("coord", ["hip_{}_flex", "shoulder_{}_flex"])
def test_left_origin_is_plus_y_right_minus_y(
    joints: dict[str, ET.Element], coord: str
) -> None:
    first = coord.format("l")
    left = _vec(joints[first].find("origin").get("xyz", ""))  # type: ignore[union-attr]
    right = _vec(joints[coord.format("r")].find("origin").get("xyz", ""))  # type: ignore[union-attr]
    assert left[1] > 0.0 > right[1]
    assert left[1] == pytest.approx(-right[1])


def test_barbell_left_sleeve_is_plus_y() -> None:
    root = ET.fromstring(build_squat_model())
    welds = {j.get("name"): j for j in root.findall("joint")}
    left = welds["barbell_left_weld"].find("origin").get("xyz", "")  # type: ignore[union-attr]
    right = welds["barbell_right_weld"].find("origin").get("xyz", "")  # type: ignore[union-attr]
    assert _vec(left)[1] > 0.0 > _vec(right)[1]
