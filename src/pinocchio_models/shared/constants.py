"""Named constants for joint limits and physics parameters.

Centralizes magic numbers that were previously scattered across
body_model.py and exercise builders. All angles in radians.
"""

from __future__ import annotations

import math

# --- Joint range-of-motion limits (radians) ---
# Lumbar spine (flexion/extension about Y)
LUMBAR_FLEXION_MIN: float = -math.radians(30)  # -0.5236
LUMBAR_FLEXION_MAX: float = math.radians(45)  # 0.7854

# Neck (flexion/extension about Y)
NECK_FLEXION_MIN: float = -math.radians(30)  # -0.5236
NECK_FLEXION_MAX: float = math.radians(30)  # 0.5236

# Shoulder (full range sagittal plane)
SHOULDER_FLEXION_MIN: float = -math.pi  # -3.1416
SHOULDER_FLEXION_MAX: float = math.pi  # 3.1416

# Elbow (flexion only, 0 to ~150 degrees)
ELBOW_FLEXION_MIN: float = 0.0
ELBOW_FLEXION_MAX: float = math.radians(150)  # 2.618

# Wrist (flexion/extension about Y)
WRIST_FLEXION_MIN: float = -math.radians(70)  # -1.2217
WRIST_FLEXION_MAX: float = math.radians(70)  # 1.2217

# Hip (flexion/extension about Y)
HIP_FLEXION_MIN: float = -math.radians(30)  # -0.5236
HIP_FLEXION_MAX: float = math.radians(120)  # 2.0944

# Knee (flexion, negative convention since leg folds backward)
KNEE_FLEXION_MIN: float = -math.radians(150)  # -2.618
KNEE_FLEXION_MAX: float = 0.0

# Ankle (dorsiflexion/plantarflexion)
ANKLE_FLEXION_MIN: float = -math.radians(45)  # -0.7854
ANKLE_FLEXION_MAX: float = math.radians(45)  # 0.7854

# --- Initial pose angles (radians) for each exercise ---
# Bench press: arms extended above chest (supine)
BENCH_PRESS_SHOULDER_ANGLE: float = math.radians(90)  # arms straight up
BENCH_PRESS_ELBOW_ANGLE: float = 0.0  # arms extended
BENCH_PRESS_HIP_ANGLE: float = 0.0  # flat on bench
BENCH_PRESS_KNEE_ANGLE: float = -math.radians(90)  # feet flat on floor

# Deadlift: hip-hinged, crouched over bar
DEADLIFT_HIP_ANGLE: float = math.radians(80)
DEADLIFT_KNEE_ANGLE: float = -math.radians(60)
DEADLIFT_LUMBAR_ANGLE: float = math.radians(10)

# Squat: standing (unrack position)
SQUAT_HIP_ANGLE: float = 0.0
SQUAT_KNEE_ANGLE: float = 0.0
SQUAT_ANKLE_ANGLE: float = 0.0

# Snatch: crouched over bar (wider grip)
SNATCH_HIP_ANGLE: float = math.radians(80)
SNATCH_KNEE_ANGLE: float = -math.radians(70)
SNATCH_LUMBAR_ANGLE: float = math.radians(15)

# Clean and jerk: crouched over bar (shoulder-width grip)
CLEAN_AND_JERK_HIP_ANGLE: float = math.radians(75)
CLEAN_AND_JERK_KNEE_ANGLE: float = -math.radians(65)
CLEAN_AND_JERK_LUMBAR_ANGLE: float = math.radians(10)

# --- Grip width fractions (fraction of shaft length from center) ---
BENCH_PRESS_GRIP_FRACTION: float = 0.3
DEADLIFT_GRIP_FRACTION: float = 0.3
SNATCH_GRIP_FRACTION: float = 0.45
CLEAN_AND_JERK_GRIP_FRACTION: float = 0.28

# --- Valid exercise names ---
VALID_EXERCISE_NAMES: frozenset[str] = frozenset(
    {
        "back_squat",
        "bench_press",
        "deadlift",
        "snatch",
        "clean_and_jerk",
    }
)
