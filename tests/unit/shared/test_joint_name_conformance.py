"""Verify joint names in generated models match canonical names from standard v2.

Ref: Issue #436 ("Rename elbow_l, knee_l and neck to canonical joint names").
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

import pytest

from pinocchio_models import (
    build_bench_press_model,
    build_clean_and_jerk_model,
    build_deadlift_model,
    build_gait_model,
    build_sit_to_stand_model,
    build_snatch_model,
    build_squat_model,
)
from pinocchio_models.shared.body.body_model import create_full_body
from pinocchio_models.shared.parity._canonical import conformance

STD = conformance.load_standard()
EXPECTED_COORDS = conformance.expected_coordinates(STD)

EXERCISE_BUILDERS = {
    "bench_press": build_bench_press_model,
    "clean_and_jerk": build_clean_and_jerk_model,
    "deadlift": build_deadlift_model,
    "gait": build_gait_model,
    "sit_to_stand": build_sit_to_stand_model,
    "snatch": build_snatch_model,
    "squat": build_squat_model,
}

LEGACY_JOINT_NAMES = {"neck", "elbow_l", "elbow_r", "knee_l", "knee_r"}
CANONICAL_RENAMED_JOINTS = {
    "neck_flex",
    "elbow_l_flex",
    "elbow_r_flex",
    "knee_l_flex",
    "knee_r_flex",
}


def test_full_body_contains_canonical_joint_names_and_no_legacy() -> None:
    robot = ET.Element("robot")
    create_full_body(robot)
    joint_names = {j.get("name") for j in robot.findall("joint")}

    # Assert canonical names are present
    missing = CANONICAL_RENAMED_JOINTS - joint_names
    assert not missing, f"Missing canonical joints in full-body model: {missing}"

    # Assert no legacy names exist
    found_legacy = LEGACY_JOINT_NAMES.intersection(joint_names)
    assert not found_legacy, (
        f"Found legacy joint names in full-body model: {found_legacy}"
    )


@pytest.mark.parametrize("exercise_name, builder", EXERCISE_BUILDERS.items())
def test_all_exercise_models_have_canonical_joint_names(
    exercise_name: str, builder: object
) -> None:
    urdf_str = builder()  # type: ignore[operator]
    root = ET.fromstring(urdf_str)
    joint_names = {j.get("name") for j in root.findall("joint")}

    missing = CANONICAL_RENAMED_JOINTS - joint_names
    assert not missing, f"Exercise {exercise_name} missing canonical joints: {missing}"

    found_legacy = LEGACY_JOINT_NAMES.intersection(joint_names)
    assert not found_legacy, (
        f"Exercise {exercise_name} has legacy joint names: {found_legacy}"
    )
