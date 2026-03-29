"""Named constants for joint limits and physics parameters.

Centralizes magic numbers that were previously scattered across
body_model.py and exercise builders. All angles in radians.

Joint range-of-motion limits are based on:
  Winter, D.A. (2009). Biomechanics and Motor Control of Human Movement,
  4th edition. Wiley. ISBN 978-0-470-39818-0.
"""

from __future__ import annotations

import math

# --- Joint range-of-motion limits (radians) ---
# Winter (2009) anatomically validated ranges.

# Lumbar spine (flexion/extension about X-axis)
# Kapandji (2008) cites ~20-35 deg extension; deadlift lockout requires >10 deg.
LUMBAR_FLEXION_MIN: float = math.radians(-25)  # Extension ~25 deg
LUMBAR_FLEXION_MAX: float = math.radians(
    60
)  # Flexion ~60 deg (floor pulls require >45°; fixes #63)

# Lumbar lateral bending (about Z-axis) -- Kapandji (2008)
# ~20 deg each side
LUMBAR_LATERAL_MIN: float = math.radians(-20)  # Left lateral bend
LUMBAR_LATERAL_MAX: float = math.radians(20)  # Right lateral bend

# Lumbar axial rotation (about Y-axis) -- Kapandji (2008)
# ~5-10 deg each side (limited by facet joint orientation)
LUMBAR_ROTATION_MIN: float = math.radians(-10)  # Left rotation
LUMBAR_ROTATION_MAX: float = math.radians(10)  # Right rotation

# Neck (flexion/extension about Y)
# Winter (2009) cites ~50-70° flexion and ~60° extension.
NECK_FLEXION_MIN: float = math.radians(-60)  # Extension ~60 deg
NECK_FLEXION_MAX: float = math.radians(70)  # Flexion ~70 deg

# Shoulder (sagittal plane flexion/extension)
# Extension: -30 deg; Full flexion: 180 deg -- Winter (2009)
SHOULDER_FLEXION_MIN: float = math.radians(-30)  # Extension
SHOULDER_FLEXION_MAX: float = math.radians(180)  # Full flexion

# Shoulder adduction/abduction (frontal plane, about Z-axis)
# Kapandji (2008): adduction ~30 deg, abduction ~180 deg
SHOULDER_ADDUCTION_MIN: float = -0.5236  # -30 deg (adduction past midline)
SHOULDER_ADDUCTION_MAX: float = 3.1416  # 180 deg (full abduction)

# Shoulder internal/external rotation (about Y-axis, long axis of humerus)
# Kapandji (2008): ~90 deg internal, ~90 deg external
SHOULDER_ROTATION_MIN: float = -1.5708  # -90 deg (external rotation)
SHOULDER_ROTATION_MAX: float = 1.5708  # 90 deg (internal rotation)

# Elbow (flexion only, 0 to ~150 degrees)
ELBOW_FLEXION_MIN: float = math.radians(0)
ELBOW_FLEXION_MAX: float = math.radians(150)  # 2.618

# Wrist (flexion/extension about Y) -- Winter (2009)
WRIST_FLEXION_MIN: float = math.radians(-80)  # Extension
WRIST_FLEXION_MAX: float = math.radians(70)  # Flexion

# Wrist radial/ulnar deviation (about Z-axis) -- Winter (2009)
# Radial deviation ~20 deg, ulnar deviation ~30 deg
WRIST_DEVIATION_MIN: float = -0.3491  # -20 deg (radial deviation)
WRIST_DEVIATION_MAX: float = 0.5236  # 30 deg (ulnar deviation)

# Hip (flexion/extension about Y) -- Winter (2009)
HIP_FLEXION_MIN: float = math.radians(-30)  # Extension
HIP_FLEXION_MAX: float = math.radians(120)  # Flexion 2.0944

# Hip adduction/abduction (frontal plane, about Z-axis)
# Kapandji (2008): adduction ~30 deg, abduction ~45 deg
HIP_ADDUCTION_MIN: float = -0.7854  # -45 deg (abduction)
HIP_ADDUCTION_MAX: float = 0.5236  # 30 deg (adduction)

# Hip internal/external rotation (about Y-axis, long axis of femur)
# Kapandji (2008): ~45 deg internal, ~45 deg external
HIP_ROTATION_MIN: float = -0.7854  # -45 deg (external rotation)
HIP_ROTATION_MAX: float = 0.7854  # 45 deg (internal rotation)

# Knee (flexion, negative convention since leg folds backward) -- Winter (2009)
KNEE_FLEXION_MIN: float = math.radians(-150)  # Full flexion -2.618
KNEE_FLEXION_MAX: float = math.radians(0)

# Ankle (dorsiflexion/plantarflexion) -- Winter (2009)
ANKLE_FLEXION_MIN: float = math.radians(-50)  # Plantarflexion
ANKLE_FLEXION_MAX: float = math.radians(20)  # Dorsiflexion

# Ankle inversion/eversion (about longitudinal foot axis) -- Winter (2009)
# Inversion ~20 deg, eversion ~20 deg
ANKLE_INVERSION_MIN: float = -0.3491  # -20 deg (eversion)
ANKLE_INVERSION_MAX: float = 0.3491  # 20 deg (inversion)

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
DEADLIFT_ANKLE_ANGLE: float = math.radians(18)  # Dorsiflexion at setup

# Squat: standing (unrack position)
SQUAT_HIP_ANGLE: float = 0.0
SQUAT_KNEE_ANGLE: float = 0.0
SQUAT_ANKLE_ANGLE: float = 0.0

# Snatch: crouched over bar (wider grip)
SNATCH_HIP_ANGLE: float = math.radians(80)
SNATCH_KNEE_ANGLE: float = -math.radians(70)
SNATCH_LUMBAR_ANGLE: float = math.radians(15)
SNATCH_ANKLE_ANGLE: float = math.radians(20)  # Dorsiflexion at setup (wider stance)

# Clean and jerk: crouched over bar (shoulder-width grip)
CLEAN_AND_JERK_HIP_ANGLE: float = math.radians(75)
CLEAN_AND_JERK_KNEE_ANGLE: float = -math.radians(65)
CLEAN_AND_JERK_LUMBAR_ANGLE: float = math.radians(10)
CLEAN_AND_JERK_ANKLE_ANGLE: float = math.radians(18)  # Dorsiflexion at setup

# Gait: natural standing (mid-stance ready position)
GAIT_HIP_ANGLE: float = math.radians(5)  # Slight flexion
GAIT_KNEE_ANGLE: float = -math.radians(5)  # Slight flexion
GAIT_ANKLE_ANGLE: float = 0.0  # Neutral

# Sit-to-stand: seated position (~90 deg hip/knee flexion)
STS_HIP_ANGLE: float = math.radians(90)
STS_KNEE_ANGLE: float = -math.radians(90)
STS_ANKLE_ANGLE: float = math.radians(15)  # Slight dorsiflexion

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
        "gait",
        "sit_to_stand",
    }
)

# --- Body geometry proportionality constants ---
# Anthropometric proportionalities derived from:
# Drillis, R., & Contini, R. (1966). Body Segment Parameters. Report no. 1166-03.
# and Winter, D. A. (2009). Biomechanics and Motor Control of Human Movement.

# Shoulder height along the torso as a fraction of torso length.
# Approximates the C7/T1 joint center relative to the full torso segment.
SHOULDER_HEIGHT_FRAC: float = 0.82  # Adjust from 0.95 to better align with Winter

# Shoulder lateral offset (biacromial breadth half-width) as a fraction of total height.
# Biacromial breadth is approx 0.259 * height for standard male (Drillis & Contini).
# Since our coordinate system evaluates from center, we use half this breadth.
SHOULDER_LATERAL_FRAC_OF_HEIGHT: float = 0.1295

# Hip lateral offset (bi-iliocristal breadth half-width) as a fraction of total height.
# Bi-iliocristal breadth is approx 0.191 * height for standard male (Drillis & Contini).
HIP_LATERAL_FRAC_OF_HEIGHT: float = 0.0955
