"""Example: visualize a squat model with Gepetto viewer.

This example shows how to load a URDF model and display it
using the gepetto_viewer integration provided by pinocchio_models.
"""

from pathlib import Path

from pinocchio_models.addons.gepetto.viewer import GepettoVisualizer


def main() -> int:
    """Load and display a squat model."""
    script_dir = Path(__file__).resolve().parent
    urdf_path = script_dir / ".." / "models" / "back_squat.urdf"

    if not urdf_path.exists():
        print(f"URDF not found at {urdf_path}")
        print("Run 'python examples/generate_all_models.py' first.")
        return 1

    print("Loading model for visualization...")
    visualizer = GepettoVisualizer(str(urdf_path))
    print("Starting viewer (press Ctrl+C to stop)...")
    visualizer.run()

    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())