"""CLI entry point for Pinocchio model generation.

Usage::

    python3 -m pinocchio_models squat
    python3 -m pinocchio_models bench_press --mass 90 --height 1.80 --plates 60
    python3 -m pinocchio_models all --output-dir ./models
"""

from __future__ import annotations

import argparse
import logging
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
from pinocchio_models.shared.constants import VALID_EXERCISE_NAMES

logger = logging.getLogger(__name__)

_BUILDERS: dict[str, Callable[..., str]] = {
    "back_squat": build_squat_model,
    "bench_press": build_bench_press_model,
    "deadlift": build_deadlift_model,
    "snatch": build_snatch_model,
    "clean_and_jerk": build_clean_and_jerk_model,
    "gait": build_gait_model,
    "sit_to_stand": build_sit_to_stand_model,
}


def _create_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="pinocchio-models",
        description="Generate Pinocchio URDF models for barbell exercises.",
    )
    parser.add_argument(
        "exercise",
        choices=[*sorted(VALID_EXERCISE_NAMES), "all"],
        help="Exercise to generate (or 'all' for all exercises).",
    )
    parser.add_argument(
        "--mass",
        type=float,
        default=80.0,
        help="Body mass in kg (default: 80.0).",
    )
    parser.add_argument(
        "--height",
        type=float,
        default=1.75,
        help="Body height in meters (default: 1.75).",
    )
    parser.add_argument(
        "--plates",
        type=float,
        default=0.0,
        help="Plate mass per side in kg (default: 0.0).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to write URDF files (default: stdout).",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser


def _validate_cli_args(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> None:
    """DbC: validate numeric CLI arguments and exit via *parser* on failure."""
    if args.mass <= 0:
        parser.error(f"--mass must be positive, got {args.mass}")
    if args.height <= 0:
        parser.error(f"--height must be positive, got {args.height}")
    if args.plates < 0:
        parser.error(f"--plates must be non-negative, got {args.plates}")


def _emit_urdf(exercise_name: str, urdf_str: str, output_dir: Path | None) -> None:
    """Write *urdf_str* either to ``<output_dir>/<exercise>.urdf`` or stdout."""
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{exercise_name}.urdf"
        out_path.write_text(urdf_str, encoding="utf-8")
        logger.info("Wrote %s", out_path)
    else:
        stdout = sys.stdout
        stdout.write(urdf_str)
        stdout.write("\n")


def main(argv: list[str] | None = None) -> int:
    """CLI entry point for Pinocchio model generation.

    Args:
        argv: Argument list (uses sys.argv if None).

    Returns:
        Exit code: 0 on success.
    """
    parser = _create_parser()
    args = parser.parse_args(argv)
    _validate_cli_args(parser, args)

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.WARNING,
        format="%(levelname)s: %(message)s",
    )

    exercises = (
        sorted(VALID_EXERCISE_NAMES) if args.exercise == "all" else [args.exercise]
    )

    for exercise_name in exercises:
        builder_fn = _BUILDERS[exercise_name]
        logger.info("Generating %s model", exercise_name)
        urdf_str = builder_fn(
            body_mass=args.mass,
            height=args.height,
            plate_mass_per_side=args.plates,
        )
        _emit_urdf(exercise_name, urdf_str, args.output_dir)

    return 0


if __name__ == "__main__":
    sys.exit(main())
