"""Unit tests for the standard-derived joint axes and origins (issue #435)."""

from __future__ import annotations

import math

import pytest

from pinocchio_models.exceptions import GeometryError
from pinocchio_models.shared.body.canonical_topology import (
    joint_axis,
    joint_offset,
    solve_grip_abduction,
)


def test_right_and_left_axes_are_mirrored_only_where_the_standard_says() -> None:
    assert joint_axis("hip_l_flex") == joint_axis("hip_r_flex") == (0.0, -1.0, 0.0)
    assert joint_axis("hip_l_adduct") == (-1.0, 0.0, 0.0)
    assert joint_axis("hip_r_adduct") == (1.0, 0.0, 0.0)
    assert joint_axis("shoulder_l_rotate") == (0.0, 0.0, -1.0)
    assert joint_axis("lumbar_flex") == (0.0, 1.0, 0.0)


def test_unknown_coordinate_raises() -> None:
    with pytest.raises(KeyError):
        joint_axis("hip_l_wiggle")


def test_default_body_offsets_match_the_standard_numbers() -> None:
    assert joint_offset("thigh_l", 1.75) == pytest.approx((0.0, 0.08925, -0.0875))
    assert joint_offset("thigh_r", 1.75)[1] == pytest.approx(-0.08925)
    assert joint_offset("upper_arm_l", 1.75)[1] == pytest.approx(0.168)
    assert joint_offset("torso", 1.75) == pytest.approx((0.0, 0.0, 0.0875))


def test_offsets_scale_linearly_with_height() -> None:
    base = joint_offset("forearm_l", 1.75)
    assert joint_offset("forearm_l", 3.5) == pytest.approx(tuple(2 * v for v in base))


def test_solve_grip_abduction_matches_shoulder_width_at_zero_angle() -> None:
    """Requesting exactly the neutral shoulder width needs zero abduction."""
    shoulder_y = joint_offset("upper_arm_l", 1.75)[1]
    assert solve_grip_abduction(shoulder_y, 1.75) == pytest.approx(0.0, abs=1e-9)


def test_solve_grip_abduction_widens_hand_for_wider_grip() -> None:
    """A grip wider than the shoulder needs a negative (abducting) angle."""
    shoulder_y = joint_offset("upper_arm_l", 1.75)[1]
    theta = solve_grip_abduction(shoulder_y + 0.2, 1.75)
    assert theta < 0.0


def test_solve_grip_abduction_matches_closed_form() -> None:
    """The angle satisfies the shoulder-to-hand rigid-rotation equation exactly."""
    height = 1.75
    shoulder_y = joint_offset("upper_arm_l", height)[1]
    arm_length = (
        -joint_offset("forearm_l", height)[2] - joint_offset("hand_l", height)[2]
    )
    grip = 0.393
    theta = solve_grip_abduction(grip, height)
    assert shoulder_y - arm_length * math.sin(theta) == pytest.approx(grip)


def test_solve_grip_abduction_rejects_non_positive_width() -> None:
    with pytest.raises(ValueError, match="positive"):
        solve_grip_abduction(0.0, 1.75)


def test_solve_grip_abduction_rejects_unreachable_grip() -> None:
    """A grip far wider than shoulder + arm length cannot be reached."""
    with pytest.raises(GeometryError):
        solve_grip_abduction(10.0, 1.75)
