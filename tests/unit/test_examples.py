"""Regression tests for the runnable examples shipped with the project."""

from __future__ import annotations

import ast
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXAMPLES = ROOT / "examples"


def test_optional_addon_examples_are_present() -> None:
    """Keep one focused example for each documented optional addon."""
    expected = {
        "gepetto_visualization.py",
        "pink_inverse_kinematics.py",
        "crocoddyl_optimal_control.py",
    }

    actual = {path.name for path in EXAMPLES.glob("*.py")}

    assert expected <= actual


def test_examples_parse_as_python() -> None:
    """Examples should at least remain syntactically valid."""
    for path in EXAMPLES.glob("*.py"):
        ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
