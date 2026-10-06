"""Unit tests for the standard-derived joint axes and origins (issue #435)."""

from __future__ import annotations

import pytest

from pinocchio_models.shared.body.canonical_topology import joint_axis, joint_offset


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
