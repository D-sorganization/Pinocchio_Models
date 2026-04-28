"""Basic usage example: load a model and print joint names.

This example demonstrates the core functionality of pinocchio_models:
loading a URDF model and inspecting its structure.
"""

from pathlib import Path

import pinocchio as pin


def main() -> int:
    """Load a squat model and print joint information."""
    # Find the squat URDF relative to this script
    script_dir = Path(__file__).resolve().parent
    urdf_path = script_dir / ".." / "models" / "back_squat.urdf"

    if not urdf_path.exists():
        print(f"URDF not found at {urdf_path}")
        print("Run 'python examples/generate_all_models.py' first.")
        return 1

    model = pin.buildModelFromUrdf(str(urdf_path))
    print(f"Loaded model: {model.name}")
    print(f"Number of joints: {model.njoints}")
    print("\nJoint names:")
    for i in range(model.njoints):
        joint = model.joints[i]
        print(f"  {i}: {model.names[i]} (type: {joint.shortname()})")

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
