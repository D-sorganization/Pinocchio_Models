"""Tests for named constants module."""

from __future__ import annotations

import math

from pinocchio_models.shared.constants import (
    ANKLE_FLEXION_MAX,
    ANKLE_FLEXION_MIN,
    ANKLE_INVERSION_MAX,
    ANKLE_INVERSION_MIN,
    ELBOW_FLEXION_MAX,
    ELBOW_FLEXION_MIN,
    HIP_ADDUCTION_MAX,
    HIP_ADDUCTION_MIN,
    HIP_FLEXION_MAX,
    HIP_FLEXION_MIN,
    HIP_ROTATION_MAX,
    HIP_ROTATION_MIN,
    KNEE_FLEXION_MAX,
    KNEE_FLEXION_MIN,
    LUMBAR_FLEXION_MAX,
    LUMBAR_FLEXION_MIN,
    LUMBAR_LATERAL_MAX,
    LUMBAR_LATERAL_MIN,
    LUMBAR_ROTATION_MAX,
    LUMBAR_ROTATION_MIN,
    NECK_FLEXION_MAX,
    NECK_FLEXION_MIN,
    SHOULDER_ADDUCTION_MAX,
    SHOULDER_ADDUCTION_MIN,
    SHOULDER_FLEXION_MAX,
    SHOULDER_FLEXION_MIN,
    SHOULDER_ROTATION_MAX,
    SHOULDER_ROTATION_MIN,
    VALID_EXERCISE_NAMES,
    WRIST_DEVIATION_MAX,
    WRIST_DEVIATION_MIN,
    WRIST_FLEXION_MAX,
    WRIST_FLEXION_MIN,
)


class TestJointLimitConstants:
    def test_all_limits_have_lower_less_than_upper(self) -> None:
        pairs = [
            (LUMBAR_FLEXION_MIN, LUMBAR_FLEXION_MAX, "lumbar_flex"),
            (LUMBAR_LATERAL_MIN, LUMBAR_LATERAL_MAX, "lumbar_lateral"),
            (LUMBAR_ROTATION_MIN, LUMBAR_ROTATION_MAX, "lumbar_rotation"),
            (NECK_FLEXION_MIN, NECK_FLEXION_MAX, "neck"),
            (SHOULDER_FLEXION_MIN, SHOULDER_FLEXION_MAX, "shoulder_flex"),
            (SHOULDER_ADDUCTION_MIN, SHOULDER_ADDUCTION_MAX, "shoulder_adduct"),
            (SHOULDER_ROTATION_MIN, SHOULDER_ROTATION_MAX, "shoulder_rotate"),
            (ELBOW_FLEXION_MIN, ELBOW_FLEXION_MAX, "elbow"),
            (WRIST_FLEXION_MIN, WRIST_FLEXION_MAX, "wrist_flex"),
            (WRIST_DEVIATION_MIN, WRIST_DEVIATION_MAX, "wrist_deviate"),
            (HIP_FLEXION_MIN, HIP_FLEXION_MAX, "hip_flex"),
            (HIP_ADDUCTION_MIN, HIP_ADDUCTION_MAX, "hip_adduct"),
            (HIP_ROTATION_MIN, HIP_ROTATION_MAX, "hip_rotate"),
            (KNEE_FLEXION_MIN, KNEE_FLEXION_MAX, "knee"),
            (ANKLE_FLEXION_MIN, ANKLE_FLEXION_MAX, "ankle_flex"),
            (ANKLE_INVERSION_MIN, ANKLE_INVERSION_MAX, "ankle_invert"),
        ]
        for lower, upper, name in pairs:
            assert lower < upper, f"{name}: {lower} >= {upper}"

    def test_all_limits_within_physically_plausible_range(self) -> None:
        """No joint should exceed +/- 2*pi radians."""
        all_limits = [
            LUMBAR_FLEXION_MIN,
            LUMBAR_FLEXION_MAX,
            LUMBAR_LATERAL_MIN,
            LUMBAR_LATERAL_MAX,
            LUMBAR_ROTATION_MIN,
            LUMBAR_ROTATION_MAX,
            NECK_FLEXION_MIN,
            NECK_FLEXION_MAX,
            SHOULDER_FLEXION_MIN,
            SHOULDER_FLEXION_MAX,
            SHOULDER_ADDUCTION_MIN,
            SHOULDER_ADDUCTION_MAX,
            SHOULDER_ROTATION_MIN,
            SHOULDER_ROTATION_MAX,
            ELBOW_FLEXION_MIN,
            ELBOW_FLEXION_MAX,
            WRIST_FLEXION_MIN,
            WRIST_FLEXION_MAX,
            WRIST_DEVIATION_MIN,
            WRIST_DEVIATION_MAX,
            HIP_FLEXION_MIN,
            HIP_FLEXION_MAX,
            HIP_ADDUCTION_MIN,
            HIP_ADDUCTION_MAX,
            HIP_ROTATION_MIN,
            HIP_ROTATION_MAX,
            KNEE_FLEXION_MIN,
            KNEE_FLEXION_MAX,
            ANKLE_FLEXION_MIN,
            ANKLE_FLEXION_MAX,
            ANKLE_INVERSION_MIN,
            ANKLE_INVERSION_MAX,
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
