"""Cross-repo parity compliance tests.

Ensures canonical biomechanical parameters match the fleet-wide standard.
"""

from __future__ import annotations

import math

from pinocchio_models.shared.parity.standard import (
    EXERCISE_PHASE_COUNTS,
    FOOT_CONTACT_DIMS,
    GRAVITY,
    GROUND_FRICTION,
    JOINT_LIMITS,
    MENS_BARBELL,
    SEGMENT_LENGTH_FRACTIONS,
    SEGMENT_MASS_FRACTIONS,
    STANDARD_BODY_MASS,
    STANDARD_HEIGHT,
)


class TestAnthropometricConstants:
    """Canonical anthropometric values must be exact."""

    def test_standard_body_mass(self) -> None:
        assert STANDARD_BODY_MASS == 80.0

    def test_standard_height(self) -> None:
        assert STANDARD_HEIGHT == 1.75

    def test_segment_mass_fractions_sum_with_bilateral(self) -> None:
        """Bilateral segments (limbs) are listed once; doubled they sum to ~1.0."""
        bilateral = {"upper_arm", "forearm", "hand", "thigh", "shank", "foot"}
        total = sum(
            frac * 2 if seg in bilateral else frac
            for seg, frac in SEGMENT_MASS_FRACTIONS.items()
        )
        assert abs(total - 1.0) < 0.01, f"Mass fractions sum to {total}, expected ~1.0"

    def test_segment_length_fractions_keys_match_mass(self) -> None:
        assert set(SEGMENT_MASS_FRACTIONS.keys()) == set(
            SEGMENT_LENGTH_FRACTIONS.keys()
        )

    def test_all_mass_fractions_positive(self) -> None:
        for seg, frac in SEGMENT_MASS_FRACTIONS.items():
            assert frac > 0, f"{seg} mass fraction must be positive"

    def test_all_length_fractions_positive(self) -> None:
        for seg, frac in SEGMENT_LENGTH_FRACTIONS.items():
            assert frac > 0, f"{seg} length fraction must be positive"


class TestJointLimits:
    """Joint limits must match canonical values in radians."""

    EXPECTED_JOINTS = {
        "hip_flex",
        "hip_adduct",
        "hip_rotate",
        "knee_flex",
        "ankle_flex",
        "ankle_invert",
        "shoulder_flex",
        "shoulder_adduct",
        "shoulder_rotate",
        "elbow_flex",
        "wrist_flex",
        "wrist_deviate",
        "lumbar_flex",
        "lumbar_lateral",
        "lumbar_rotate",
        "neck_flex",
    }

    def test_all_expected_joints_present(self) -> None:
        assert set(JOINT_LIMITS.keys()) == self.EXPECTED_JOINTS

    def test_limits_are_tuples_of_two(self) -> None:
        for joint, limits in JOINT_LIMITS.items():
            assert len(limits) == 2, f"{joint} must have (lower, upper)"

    def test_lower_less_than_upper(self) -> None:
        for joint, (lower, upper) in JOINT_LIMITS.items():
            assert lower < upper, f"{joint}: lower {lower} >= upper {upper}"

    def test_hip_flex_canonical(self) -> None:
        lower, upper = JOINT_LIMITS["hip_flex"]
        assert abs(lower - math.radians(-30)) < 1e-10
        assert abs(upper - math.radians(120)) < 1e-10

    def test_knee_flex_canonical(self) -> None:
        lower, upper = JOINT_LIMITS["knee_flex"]
        assert abs(lower - math.radians(-150)) < 1e-10
        assert abs(upper - math.radians(0)) < 1e-10


class TestEquipmentConstants:
    """Barbell and contact dimensions must match canonical values."""

    def test_mens_barbell_mass(self) -> None:
        assert MENS_BARBELL["bar_mass"] == 20.0

    def test_mens_barbell_length(self) -> None:
        assert MENS_BARBELL["total_length"] == 2.20

    def test_mens_barbell_shaft_length(self) -> None:
        assert MENS_BARBELL["shaft_length"] == 1.31

    def test_foot_contact_dims_keys(self) -> None:
        assert set(FOOT_CONTACT_DIMS.keys()) == {"length", "width", "height"}

    def test_foot_contact_length(self) -> None:
        assert FOOT_CONTACT_DIMS["length"] == 0.26


class TestEnvironmentConstants:
    """Friction and gravity must match canonical values."""

    def test_ground_friction_static(self) -> None:
        assert GROUND_FRICTION["static"] == 0.8

    def test_ground_friction_dynamic(self) -> None:
        assert GROUND_FRICTION["dynamic"] == 0.6

    def test_gravity_vector(self) -> None:
        assert GRAVITY == (0.0, 0.0, -9.80665)

    def test_gravity_magnitude(self) -> None:
        mag = math.sqrt(sum(g**2 for g in GRAVITY))
        assert abs(mag - 9.80665) < 1e-10


class TestExercisePhases:
    """Exercise phase counts must match canonical values."""

    def test_back_squat_phases(self) -> None:
        assert EXERCISE_PHASE_COUNTS["back_squat"] == 5

    def test_deadlift_phases(self) -> None:
        assert EXERCISE_PHASE_COUNTS["deadlift"] == 5

    def test_snatch_phases(self) -> None:
        assert EXERCISE_PHASE_COUNTS["snatch"] == 6

    def test_clean_and_jerk_phases(self) -> None:
        assert EXERCISE_PHASE_COUNTS["clean_and_jerk"] == 8

    def test_all_phase_counts_positive(self) -> None:
        for exercise, count in EXERCISE_PHASE_COUNTS.items():
            assert count > 0, f"{exercise} must have positive phase count"
