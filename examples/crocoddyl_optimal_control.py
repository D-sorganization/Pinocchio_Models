"""Example: create a Crocoddyl optimal-control problem.

This example builds a deadlift URDF in memory, creates a short Crocoddyl
shooting problem, solves it, and prints the resulting trajectory sizes.

Run with::

    python examples/crocoddyl_optimal_control.py

Requires the optional Crocoddyl extra::

    pip install -e ".[crocoddyl]"
"""

from __future__ import annotations

from importlib.util import find_spec

from pinocchio_models.exercises.deadlift.deadlift_model import build_deadlift_model


def main() -> int:
    """Build and solve a compact Crocoddyl OCP for a deadlift."""
    if find_spec("crocoddyl") is None or find_spec("pinocchio") is None:
        print("Crocoddyl and Pinocchio are not installed.")
        print('Install the optional dependency with: pip install -e ".[crocoddyl]"')
        return 1

    from pinocchio_models.addons.crocoddyl.optimal_control import (
        create_exercise_ocp,
        extract_joint_torques,
        solve_trajectory,
    )

    urdf_str = build_deadlift_model(
        body_mass=85.0,
        height=1.80,
        plate_mass_per_side=80.0,
    )

    ocp = create_exercise_ocp(
        urdf_str,
        "deadlift",
        dt=0.02,
        n_steps=20,
        use_contacts=False,
    )
    trajectory = solve_trajectory(ocp, max_iterations=20)
    torques = extract_joint_torques(trajectory, ocp)

    states, controls = trajectory
    print("Solved Crocoddyl deadlift OCP.")
    print(f"  horizon: {ocp.n_steps} steps at dt={ocp.dt}")
    print(f"  states: {len(states)}")
    print(f"  controls: {len(controls)}")
    print(f"  torque table shape: {torques.shape}")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
