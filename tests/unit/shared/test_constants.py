"""Tests for named constants module."""

from __future__ import annotations

import math

from pinocchio_models.shared.constants import (
    ANKLE_FLEXION_MAX,
    ANKLE_FLEXION_MIN,
    ELBOW_FLEXION_MAX,
    ELBOW_FLEXION_MIN,
    HIP_FLEXION_MAX,
    HIP_FLEXION_MIN,
    KNEE_FLEXION_MAX,
    KNEE_FLEXION_MIN,
    LUMBAR_FLEXION_MAX,
    LUMBAR_FLEXION_MIN,
    NECK_FLEXION_MAX,
    NECK_FLEXION_MIN,
    SHOULDER_FLEXION_MAX,
    SHOULDER_FLEXION_MIN,
    VALID_EXERCISE_NAMES,
    WRIST_FLEXION_MAX,
    WRIST_FLEXION_MIN,
)


class TestJointLimitConstants:
    def test_all_limits_have_lower_less_than_upper(self) -> None:
        pairs = [
            (LUMBAR_FLEXION_MIN, LUMBAR_FLEXION_MAX, "lumbar"),
            (NECK_FLEXION_MIN, NECK_FLEXION_MAX, "neck"),
            (SHOULDER_FLEXION_MIN, SHOULDER_FLEXION_MAX, "shoulder"),
            (ELBOW_FLEXION_MIN, ELBOW_FLEXION_MAX, "elbow"),
            (WRIST_FLEXION_MIN, WRIST_FLEXION_MAX, "wrist"),
            (HIP_FLEXION_MIN, HIP_FLEXION_MAX, "hip"),
            (KNEE_FLEXION_MIN, KNEE_FLEXION_MAX, "knee"),
            (ANKLE_FLEXION_MIN, ANKLE_FLEXION_MAX, "ankle"),
        ]
        for lower, upper, name in pairs:
            assert lower < upper, f"{name}: {lower} >= {upper}"

    def test_all_limits_within_physically_plausible_range(self) -> None:
        """No joint should exceed +/- 2*pi radians."""
        all_limits = [
            LUMBAR_FLEXION_MIN,
            LUMBAR_FLEXION_MAX,
            NECK_FLEXION_MIN,
            NECK_FLEXION_MAX,
            SHOULDER_FLEXION_MIN,
            SHOULDER_FLEXION_MAX,
            ELBOW_FLEXION_MIN,
            ELBOW_FLEXION_MAX,
            WRIST_FLEXION_MIN,
            WRIST_FLEXION_MAX,
            HIP_FLEXION_MIN,
            HIP_FLEXION_MAX,
            KNEE_FLEXION_MIN,
            KNEE_FLEXION_MAX,
            ANKLE_FLEXION_MIN,
            ANKLE_FLEXION_MAX,
        ]
        for val in all_limits:
            assert abs(val) <= 2 * math.pi


class TestValidExerciseNames:
    def test_contains_all_five_exercises(self) -> None:
        assert len(VALID_EXERCISE_NAMES) == 5
        assert "back_squat" in VALID_EXERCISE_NAMES
        assert "bench_press" in VALID_EXERCISE_NAMES
        assert "deadlift" in VALID_EXERCISE_NAMES
        assert "snatch" in VALID_EXERCISE_NAMES
        assert "clean_and_jerk" in VALID_EXERCISE_NAMES

    def test_is_frozen(self) -> None:
        assert isinstance(VALID_EXERCISE_NAMES, frozenset)
