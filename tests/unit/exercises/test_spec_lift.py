"""Unit tests for ``SpecStart``: the spec start via-pose as generator input.

LIFT-3 (UpstreamDrift#11743). Engine-free: the reference forward kinematics of
the vendored standard (``_canonical/topology``) supplies the placements; the
real-engine checks live in ``tests/parity/test_spec_start_pose.py``.
"""

from __future__ import annotations

import pytest

from pinocchio_models.exercises.spec_lift import SpecStart
from pinocchio_models.shared.parity._canonical import conformance, spec

STD = conformance.load_standard()
HEIGHT = float(STD["anthropometrics"]["height_m"])


def test_unknown_exercise_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown exercise"):
        SpecStart("curl", HEIGHT)


def test_exercise_without_a_start_via_pose_is_rejected() -> None:
    with pytest.raises(ValueError, match="no via-pose 'start'"):
        SpecStart("gait", HEIGHT)


@pytest.mark.parametrize("height", [0.0, -1.75])
def test_non_positive_height_is_rejected(height: float) -> None:
    with pytest.raises(ValueError, match="height"):
        SpecStart("deadlift", height)


def test_coordinates_use_engine_joint_names_and_zero_unlisted() -> None:
    coords = SpecStart("deadlift", HEIGHT).coordinates()
    want = spec.pose_coordinates(STD, "deadlift", "start")
    assert coords["knee_l"] == want["knee_l_flex"]  # engine name of knee_l_flex
    assert coords["hip_r_flex"] == want["hip_r_flex"]
    assert coords["elbow_l"] == 0.0  # not listed in the deadlift start
    assert coords["neck"] == want["neck_flex"]
    assert len(coords) == len(conformance.expected_coordinates(STD))


def test_root_is_the_spec_root_at_the_standard_height() -> None:
    root = spec.exercise_spec(STD, "snatch")["via_poses"]["start"]["root"]
    xyz, rpy = SpecStart("snatch", HEIGHT).root()
    assert xyz == pytest.approx(tuple(root["position_m"]))
    assert rpy == pytest.approx(tuple(root["orientation_rpy_rad"]))


def test_positions_scale_linearly_with_height_and_angles_do_not() -> None:
    base, tall = SpecStart("squat", HEIGHT), SpecStart("squat", 2.0 * HEIGHT)
    assert tall.root()[0] == pytest.approx(tuple(2.0 * v for v in base.root()[0]))
    assert tall.root()[1] == pytest.approx(base.root()[1])
    assert tall.bar_in("torso")[0] == pytest.approx(
        tuple(2.0 * v for v in base.bar_in("torso")[0])
    )
    assert tall.grip_half_width_m == pytest.approx(2.0 * base.grip_half_width_m)
    assert tall.coordinates() == base.coordinates()


def test_grip_half_width_is_half_the_spec_width() -> None:
    width = spec.exercise_spec(STD, "bench_press")["grip"]["width_m"]
    assert SpecStart("bench_press", HEIGHT).grip_half_width_m == width / 2.0


def test_bar_in_an_unknown_segment_is_rejected() -> None:
    with pytest.raises(ValueError, match="segment"):
        SpecStart("deadlift", HEIGHT).bar_in("barbell")
