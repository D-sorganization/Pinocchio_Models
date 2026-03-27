"""Cross-repo parity standard — canonical biomechanical parameters.

Joint limits are derived from ``constants.py`` (the single source of
truth, cited from Winter 2009 and Kapandji 2008). This module
re-exports those values in a dictionary form suitable for cross-repo
parity checks.
"""

from __future__ import annotations

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
    WRIST_DEVIATION_MAX,
    WRIST_DEVIATION_MIN,
    WRIST_FLEXION_MAX,
    WRIST_FLEXION_MIN,
)

STANDARD_BODY_MASS = 80.0
STANDARD_HEIGHT = 1.75

SEGMENT_MASS_FRACTIONS = {
    "pelvis": 0.142,
    "torso": 0.355,
    "head": 0.081,
    "upper_arm": 0.028,
    "forearm": 0.016,
    "hand": 0.006,
    "thigh": 0.100,
    "shank": 0.047,
    "foot": 0.014,
}

SEGMENT_LENGTH_FRACTIONS = {
    "pelvis": 0.100,
    "torso": 0.288,
    "head": 0.130,
    "upper_arm": 0.186,
    "forearm": 0.146,
    "hand": 0.050,
    "thigh": 0.245,
    "shank": 0.246,
    "foot": 0.040,
}

# Derived from constants.py — single source of truth for joint limits.
JOINT_LIMITS = {
    "hip_flex": (HIP_FLEXION_MIN, HIP_FLEXION_MAX),
    "hip_adduct": (HIP_ADDUCTION_MIN, HIP_ADDUCTION_MAX),
    "hip_rotate": (HIP_ROTATION_MIN, HIP_ROTATION_MAX),
    "knee_flex": (KNEE_FLEXION_MIN, KNEE_FLEXION_MAX),
    "ankle_flex": (ANKLE_FLEXION_MIN, ANKLE_FLEXION_MAX),
    "ankle_invert": (ANKLE_INVERSION_MIN, ANKLE_INVERSION_MAX),
    "shoulder_flex": (SHOULDER_FLEXION_MIN, SHOULDER_FLEXION_MAX),
    "shoulder_adduct": (SHOULDER_ADDUCTION_MIN, SHOULDER_ADDUCTION_MAX),
    "shoulder_rotate": (SHOULDER_ROTATION_MIN, SHOULDER_ROTATION_MAX),
    "elbow_flex": (ELBOW_FLEXION_MIN, ELBOW_FLEXION_MAX),
    "wrist_flex": (WRIST_FLEXION_MIN, WRIST_FLEXION_MAX),
    "wrist_deviate": (WRIST_DEVIATION_MIN, WRIST_DEVIATION_MAX),
    "lumbar_flex": (LUMBAR_FLEXION_MIN, LUMBAR_FLEXION_MAX),
    "lumbar_lateral": (LUMBAR_LATERAL_MIN, LUMBAR_LATERAL_MAX),
    "lumbar_rotate": (LUMBAR_ROTATION_MIN, LUMBAR_ROTATION_MAX),
    "neck_flex": (NECK_FLEXION_MIN, NECK_FLEXION_MAX),
}

MENS_BARBELL = {
    "total_length": 2.20,
    "shaft_length": 1.31,
    "shaft_diameter": 0.028,
    "sleeve_diameter": 0.050,
    "bar_mass": 20.0,
}

FOOT_CONTACT_DIMS = {
    "length": 0.26,
    "width": 0.10,
    "height": 0.02,
}

GROUND_FRICTION = {
    "static": 0.8,
    "dynamic": 0.6,
}

# Phase counts derived from exercise_objectives.py — the authoritative
# source for the number of optimisation phases in each exercise.
EXERCISE_PHASE_COUNTS = {
    "back_squat": 5,
    "deadlift": 4,
    "bench_press": 5,
    "snatch": 6,
    "clean_and_jerk": 8,
    "gait": 8,
    "sit_to_stand": 6,
}

GRAVITY = (0.0, 0.0, -9.80665)
