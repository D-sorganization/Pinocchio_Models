"""Test conformance of URDF joint limits against biomech_parity_standard.json.

Ensures zero joint-limit divergence ledger entries in Pinocchio_Models (Issue #433).
"""

from __future__ import annotations

import math
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

from pinocchio_models import (
    build_bench_press_model,
    build_clean_and_jerk_model,
    build_deadlift_model,
    build_gait_model,
    build_sit_to_stand_model,
    build_snatch_model,
    build_squat_model,
)
from pinocchio_models.shared.parity._canonical import conformance

STD = conformance.load_standard()
EXPECTED_COORDS = conformance.expected_coordinates(STD)
TOL = STD["tolerances"]["limit_abs_rad"]

EXERCISES = {
    "squat": build_squat_model,
    "deadlift": build_deadlift_model,
    "bench_press": build_bench_press_model,
    "snatch": build_snatch_model,
    "clean_and_jerk": build_clean_and_jerk_model,
    "gait": build_gait_model,
    "sit_to_stand": build_sit_to_stand_model,
}


def _extract_urdf_joint_limits(urdf_str: str) -> dict[str, tuple[float, float]]:
    """Extract lower and upper limits in radians for all 1-DOF joints in the URDF."""
    root = ET.fromstring(urdf_str)
    limits: dict[str, tuple[float, float]] = {}
    for joint in root.findall("joint"):
        name = joint.get("name")
        if not name or joint.get("type") in ("fixed", "floating"):
            continue
        limit_el = joint.find("limit")
        if limit_el is not None:
            lower = float(limit_el.get("lower", "0.0"))
            upper = float(limit_el.get("upper", "0.0"))
            limits[name] = (lower, upper)
    return limits


@pytest.mark.parametrize("exercise_name,builder", EXERCISES.items())
def test_urdf_joint_limits_match_parity_standard(
    exercise_name: str, builder: object
) -> None:
    """Every revolute joint in each exercise model must strictly match standard limits."""
    urdf = builder()  # type: ignore[operator]
    urdf_limits = _extract_urdf_joint_limits(urdf)

    mismatches: list[str] = []
    for coord_name, (expected_lo, expected_hi) in EXPECTED_COORDS.items():
        if coord_name not in urdf_limits:
            mismatches.append(f"Missing coordinate {coord_name} in {exercise_name}")
            continue
        got_lo, got_hi = urdf_limits[coord_name]
        if not (
            math.isclose(got_lo, expected_lo, abs_tol=TOL)
            and math.isclose(got_hi, expected_hi, abs_tol=TOL)
        ):
            mismatches.append(
                f"{coord_name}: got [{got_lo:.4f}, {got_hi:.4f}] rad "
                f"([{math.degrees(got_lo):.1f}, {math.degrees(got_hi):.1f}] deg) != "
                f"expected [{expected_lo:.4f}, {expected_hi:.4f}] rad "
                f"([{math.degrees(expected_lo):.1f}, {math.degrees(expected_hi):.1f}] deg)"
            )

    assert not mismatches, f"Joint limit mismatches in {exercise_name}:\n" + "\n".join(
        mismatches
    )


def test_parity_divergences_ledger_has_no_joint_limit_entries() -> None:
    """The parity_divergences.json ledger must contain zero coordinate limit deviations."""
    ledger_path = (
        Path(__file__).parents[3]
        / "src"
        / "pinocchio_models"
        / "shared"
        / "parity"
        / "parity_divergences.json"
    )
    ledger = conformance.load_ledger(ledger_path)
    divergences = ledger.get("divergences", {})
    coordinate_divergences = [
        k for k in divergences if "limits_rad" in k or k.startswith("coordinate.")
    ]
    assert not coordinate_divergences, (
        f"Found coordinate limit divergences in ledger that must be resolved: {coordinate_divergences}"
    )
