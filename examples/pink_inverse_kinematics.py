"""Example: compute exercise keyframes with the Pink IK addon.

This example builds a squat URDF in memory, then asks the Pink integration
to generate a small set of keyframe configurations for the lift.

Run with::

    python examples/pink_inverse_kinematics.py

Requires the optional Pink extra::

    pip install -e ".[pink]"
"""

from __future__ import annotations

from importlib.util import find_spec

from pinocchio_models.exercises.squat.squat_model import build_squat_model


def main() -> int:
    """Build a squat model and print Pink IK keyframe summaries."""
    if find_spec("pink") is None or find_spec("pinocchio") is None:
        print("Pink and Pinocchio are not installed.")
        print('Install the optional dependency with: pip install -e ".[pink]"')
        return 1

    from pinocchio_models.addons.pink.ik_solver import compute_exercise_keyframes

    urdf_str = build_squat_model(
        body_mass=80.0,
        height=1.75,
        plate_mass_per_side=60.0,
    )

    keyframes = compute_exercise_keyframes(
        urdf_str,
        "back_squat",
        n_frames=5,
    )

    print(f"Computed {len(keyframes)} Pink IK keyframes for back_squat.")
    for index, q in enumerate(keyframes, start=1):
        print(f"  keyframe {index}: nq={q.shape[0]}, first_dof={q[0]:.3f}")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
