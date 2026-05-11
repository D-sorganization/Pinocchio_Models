"""CLI entry point for Pinocchio model generation.

Usage (legacy positional form, retained for backward compatibility)::

    python3 -m pinocchio_models squat
    python3 -m pinocchio_models bench_press --mass 90 --height 1.80 --plates 60
    python3 -m pinocchio_models all --output-dir ./models

Usage (UpstreamDrift launcher contract, see issue #282)::

    python3 -m pinocchio_models --list-exercises
    python3 -m pinocchio_models --exercise gait --export /tmp/gait.urdf
"""

from __future__ import annotations

import argparse
import json
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

# Aliases from manifest-declared IDs to builder keys. The model_pack
# manifest uses the short name ``squat``; the legacy CLI keeps
# ``back_squat`` for backward compatibility.
_MANIFEST_ID_ALIASES: dict[str, str] = {
    "squat": "back_squat",
}


def _manifest_choices() -> list[str]:
    """Return the union of builder keys and manifest aliases."""
    return sorted({*VALID_EXERCISE_NAMES, *_MANIFEST_ID_ALIASES.keys()})


def _add_exercise_argument(parser: argparse.ArgumentParser) -> None:
    """Add the positional ``exercise`` argument plus ``--exercise`` flag.

    Accepts the legacy positional form as well as the
    ``--exercise <name>`` flag required by the UpstreamDrift launcher
    contract (issue #282).
    """
    parser.add_argument(
        "exercise",
        nargs="?",
        default=None,
        choices=[*_manifest_choices(), "all"],
        help="Exercise to generate (or 'all' for all exercises).",
    )
    parser.add_argument(
        "--exercise",
        dest="exercise_flag",
        choices=_manifest_choices(),
        default=None,
        help=(
            "Exercise to generate (UpstreamDrift launcher form). "
            "Mutually exclusive with the positional 'exercise' argument."
        ),
    )
    parser.add_argument(
        "--list-exercises",
        action="store_true",
        help="List the manifest-declared exercise IDs and exit.",
    )
    parser.add_argument(
        "--export",
        type=Path,
        default=None,
        help=(
            "Write the generated URDF to this file path "
            "(launcher contract: implies a single exercise selection)."
        ),
    )


def _add_anthropometry_arguments(parser: argparse.ArgumentParser) -> None:
    """Add anthropometry / loading arguments (``--mass``, ``--height``, ``--plates``)."""
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


def _add_output_arguments(parser: argparse.ArgumentParser) -> None:
    """Add output / verbosity arguments (``--output-dir``, ``--json``, ``-v``)."""
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=None,
        help="Directory to write URDF files (default: stdout).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit structured JSON output to stdout.",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )


def _create_parser() -> argparse.ArgumentParser:
    """Build the argument parser composed from focused helper groups."""
    parser = argparse.ArgumentParser(
        prog="pinocchio-models",
        description="Generate Pinocchio URDF models for barbell exercises.",
    )
    _add_exercise_argument(parser)
    _add_anthropometry_arguments(parser)
    _add_output_arguments(parser)
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
    if args.exercise is not None and args.exercise_flag is not None:
        parser.error(
            "specify the exercise either positionally or via --exercise, not both"
        )


def _resolve_exercise_selection(
    parser: argparse.ArgumentParser, args: argparse.Namespace
) -> str | None:
    """Return the canonical builder key for the requested exercise.

    Honors both the legacy positional argument and the ``--exercise``
    flag, applying manifest aliases (e.g. ``squat`` -> ``back_squat``).
    Returns ``None`` only when no selection was made (e.g. for
    ``--list-exercises``).
    """
    raw = args.exercise_flag if args.exercise_flag is not None else args.exercise
    if raw is None:
        return None
    if raw == "all":
        return "all"
    return _MANIFEST_ID_ALIASES.get(raw, raw)


def _emit_urdf(
    exercise_name: str, urdf_str: str, output_dir: Path | None
) -> str | None:
    """Write *urdf_str* either to ``<output_dir>/<exercise>.urdf`` or stdout.

    Returns the file path when written to disk, or ``None`` for stdout.
    """
    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        out_path = output_dir / f"{exercise_name}.urdf"
        out_path.write_text(urdf_str, encoding="utf-8")
        logger.info("Wrote %s", out_path)
        return str(out_path)
    stdout = sys.stdout
    stdout.write(urdf_str)
    stdout.write("\n")
    return None


def _selected_exercises(exercise: str) -> list[str]:
    """Return concrete exercise names for a single exercise or ``all``."""
    if exercise == "all":
        return sorted(VALID_EXERCISE_NAMES)
    return [exercise]


def _build_urdf_for(
    exercise_name: str,
    *,
    body_mass: float,
    height: float,
    plate_mass_per_side: float,
) -> str:
    """Build one exercise URDF from validated scalar CLI inputs."""
    builder_fn = _BUILDERS[exercise_name]
    logger.info("Generating %s model", exercise_name)
    return builder_fn(
        body_mass=body_mass,
        height=height,
        plate_mass_per_side=plate_mass_per_side,
    )


def _write_export(export_path: Path, urdf_str: str) -> None:
    """Write *urdf_str* directly to *export_path* (launcher contract)."""
    export_path.parent.mkdir(parents=True, exist_ok=True)
    export_path.write_text(urdf_str, encoding="utf-8")
    logger.info("Wrote %s", export_path)


def _emit_list_exercises() -> int:
    """Print manifest-declared exercise IDs, one per line, and return 0."""
    from pinocchio_models.model_pack import list_exercises

    sys.stdout.write("\n".join(list_exercises()))
    sys.stdout.write("\n")
    return 0


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

    if args.list_exercises:
        return _emit_list_exercises()

    canonical = _resolve_exercise_selection(parser, args)
    if canonical is None:
        parser.error(
            "an exercise must be selected via the positional argument, "
            "--exercise, or --list-exercises"
        )

    if args.export is not None and canonical == "all":
        parser.error("--export requires a single exercise (got 'all')")

    results: list[dict[str, object]] = []
    for exercise_name in _selected_exercises(canonical):
        urdf_str = _build_urdf_for(
            exercise_name,
            body_mass=args.mass,
            height=args.height,
            plate_mass_per_side=args.plates,
        )

        if args.export is not None:
            _write_export(args.export, urdf_str)
        elif not args.json:
            _emit_urdf(exercise_name, urdf_str, args.output_dir)

        if args.json:
            results.append(
                {
                    "exercise": exercise_name,
                    "urdf": urdf_str,
                    "path": (
                        str(args.export)
                        if args.export is not None
                        else (
                            str(args.output_dir / f"{exercise_name}.urdf")
                            if args.output_dir is not None
                            else None
                        )
                    ),
                    "parameters": {
                        "mass": args.mass,
                        "height": args.height,
                        "plates": args.plates,
                    },
                    "success": True,
                }
            )

    if args.json:
        json.dump(results, sys.stdout, indent=2)
        sys.stdout.write("\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
