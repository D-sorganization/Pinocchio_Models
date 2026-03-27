"""Generate all exercise URDF models and write to disk.

Usage::

    python3 examples/generate_all_models.py
    python3 examples/generate_all_models.py --output-dir ./models
"""

from __future__ import annotations

import argparse
import sys
from collections.abc import Callable
from pathlib import Path

from pinocchio_models.exercises.bench_press.bench_press_model import (
    build_bench_press_model,
)
from pinocchio_models.exercises.clean_and_jerk.clean_and_jerk_model import (
    build_clean_and_jerk_model,
)
from pinocchio_models.exercises.deadlift.deadlift_model import build_deadlift_model
from pinocchio_models.exercises.gait.gait_model import build_gait_model
from pinocchio_models.exercises.sit_to_stand.sit_to_stand_model import (
    build_sit_to_stand_model,
)
from pinocchio_models.exercises.snatch.snatch_model import build_snatch_model
from pinocchio_models.exercises.squat.squat_model import build_squat_model

EXERCISES: dict[str, Callable[..., str]] = {
    "back_squat": build_squat_model,
    "bench_press": build_bench_press_model,
    "clean_and_jerk": build_clean_and_jerk_model,
    "deadlift": build_deadlift_model,
    "gait": build_gait_model,
    "sit_to_stand": build_sit_to_stand_model,
    "snatch": build_snatch_model,
}


def main() -> int:
    """Generate all exercise URDF models."""
    parser = argparse.ArgumentParser(description="Generate all exercise URDF models.")
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("models"),
        help="Directory to write URDF files (default: ./models).",
    )
    args = parser.parse_args()

    args.output_dir.mkdir(parents=True, exist_ok=True)

    for name, builder_fn in sorted(EXERCISES.items()):
        urdf_str = builder_fn()
        out_path = args.output_dir / f"{name}.urdf"
        out_path.write_text(urdf_str, encoding="utf-8")
        print(f"Generated {out_path}")

    print(f"\nAll {len(EXERCISES)} models generated in {args.output_dir}/")
    return 0


if __name__ == "__main__":
    sys.exit(main())
