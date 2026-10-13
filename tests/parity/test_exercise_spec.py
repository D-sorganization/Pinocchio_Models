"""The lift objectives consume the vendored exercise spec (standard v2.1).

UpstreamDrift#11742 (LIFT-2), Repository_Management#2060 (Option A): phase
names, phase timing and the start, catch and lockout via-poses come from the
vendored ``biomech_parity_standard.json``, never from pack-local tables.
Standard v2.1 (Repository_Management#2077) also binds every via-pose to its
phase, so the pack keeps no pose-to-phase table (UpstreamDrift#11743).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from pinocchio_models.optimization.objectives import spec_lifts
from pinocchio_models.optimization.objectives.common import ExerciseObjective, Phase
from pinocchio_models.optimization.objectives.registry import get_exercise_objective
from pinocchio_models.shared.parity._canonical import conformance, spec
from pinocchio_models.shared.parity.fingerprint import fingerprint

STD = conformance.load_standard()
LIFTS = ("squat", "deadlift", "bench_press", "snatch", "clean_and_jerk")

# sha256 of Repository_Management/shared_scripts/model_parity/
# biomech_parity_standard.json at v2.1.0 (Repository_Management#2079).
RM_STANDARD_V2_1_SHA256 = (
    "a0eb6c2bbbfeb70011bad62cf6d21a9245ffabce757c390633b516f542eb3ef8"
)
RM_STANDARD_V2_1_CRLF_SHA256 = (
    "11377a6e1effc00c0cdefb597678d1c1847e5998e3086a0efdd5818c21f0444b"
)


def _full_pose(exercise: str, pose: str) -> dict[str, float]:
    """Every canonical coordinate of a via-pose; unlisted ones are 0 (pose_frame)."""
    out = dict.fromkeys(conformance.expected_coordinates(STD), 0.0)
    out.update(spec.pose_coordinates(STD, exercise, pose))
    return out


def test_vendored_standard_is_repository_management_v2_1() -> None:
    assert conformance.standard_sha256() in (
        RM_STANDARD_V2_1_SHA256,
        RM_STANDARD_V2_1_CRLF_SHA256,
    )
    assert STD["version"] == "2.1.0"


def _objective(exercise: str) -> ExerciseObjective:
    return get_exercise_objective(
        STD["exercises"][exercise].get("legacy_key", exercise)
    )


def _phase(objective: ExerciseObjective, name: str) -> Phase:
    return next(p for p in objective.phases if p.name == name)


ALL_EXERCISES = (
    "squat",
    "deadlift",
    "bench_press",
    "snatch",
    "clean_and_jerk",
    "gait",
    "sit_to_stand",
)


@pytest.mark.parametrize("exercise", ALL_EXERCISES)
def test_phase_names_and_timing_come_from_spec(exercise: str) -> None:
    objective = _objective(exercise)
    want = spec.exercise_spec(STD, exercise)["phases"]
    assert [p.name for p in objective.phases] == [p["name"] for p in want]
    assert [p.fraction for p in objective.phases] == [p["t_frac"] for p in want]


@pytest.mark.parametrize("exercise", ("gait", "sit_to_stand"))
def test_functional_movement_phases_conform_to_spec(exercise: str) -> None:
    """Phase names match spec, check_fingerprint clean, and no ledger entry (#467)."""
    objective = _objective(exercise)
    names = [p.name for p in objective.phases]
    assert names == spec.phase_names(STD, exercise)
    fp = {"exercise": exercise, "phase_names": names}
    assert spec.check_fingerprint(fp, STD) == []
    ledger = conformance.load_ledger(
        Path(conformance.__file__).parents[1] / "parity_divergences.json"
    )
    assert "phase_names" not in ledger.get("divergences", {})


@pytest.mark.parametrize("exercise", LIFTS)
def test_start_and_end_poses_are_spec_via_poses(exercise: str) -> None:
    objective = _objective(exercise)
    assert objective.start_pose == _full_pose(exercise, "start")
    assert objective.end_pose == _full_pose(exercise, "lockout")


@pytest.mark.parametrize("exercise", LIFTS)
def test_anchored_phases_hold_their_via_pose(exercise: str) -> None:
    objective = _objective(exercise)
    for pose in spec.exercise_spec(STD, exercise)["via_poses"]:
        phase = spec.via_pose_phase(STD, exercise, pose)
        assert _phase(objective, phase).target_joints == _full_pose(exercise, pose)


@pytest.mark.parametrize("exercise", LIFTS)
def test_start_anchors_the_first_phase(exercise: str) -> None:
    first = spec.phase_names(STD, exercise)[0]
    assert spec.via_pose_phase(STD, exercise, "start") == first
    assert _objective(exercise).phases[0].target_joints == _full_pose(exercise, "start")


def test_pack_keeps_no_local_pose_to_phase_table() -> None:
    """The binding is the spec's (RM#2077); a local copy could drift from it."""
    assert not hasattr(spec_lifts, "VIA_POSE_PHASES")


def test_unanchored_phase_is_the_blend_of_its_anchors() -> None:
    """Deadlift first_pull (t 0.10) lies between setup (0) and lockout (0.65)."""
    objective = _objective("deadlift")
    start, lockout = _full_pose("deadlift", "start"), _full_pose("deadlift", "lockout")
    w = 0.1 / 0.65
    got = _phase(objective, "first_pull").target_joints
    for name, value in got.items():
        assert value == pytest.approx(start[name] + w * (lockout[name] - start[name]))
    # After the last anchor the target holds the last anchored pose.
    assert _phase(objective, "descent").target_joints == lockout


def test_unknown_exercise_is_rejected() -> None:
    with pytest.raises(ValueError, match="unknown exercise"):
        spec_lifts.lift_objective(
            "curl", name="curl", bar_path_constraint="none", balance_mode="supine"
        )


def test_lifts_target_both_sides() -> None:
    """Spec poses set left and right limbs (fixes left-only targets, #449)."""
    for exercise in LIFTS:
        for phase in _objective(exercise).phases:
            assert (
                phase.target_joints["hip_r_flex"] == phase.target_joints["hip_l_flex"]
            )


def test_bench_press_spec_root_joint_is_weld() -> None:
    assert spec.root_joint(STD, "bench_press") == "weld"


def test_fingerprint_reports_bench_press_root_weld() -> None:
    pytest.importorskip("pinocchio")
    fp = fingerprint("bench_press")
    assert fp["root_joint"] == "weld"
