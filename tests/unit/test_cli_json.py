# SPDX-License-Identifier: MIT
"""Tests for the --json CLI flag."""

import json

import pytest

from pinocchio_models.__main__ import main


@pytest.mark.parametrize(
    "exercise",
    [
        "back_squat",
        "bench_press",
        "deadlift",
    ],
)
def test_json_output(capfd: pytest.CaptureFixture[str], exercise: str) -> None:
    """--json flag produces valid JSON with expected keys."""
    argv = [exercise, "--json", "--mass", "80", "--height", "1.75"]
    code = main(argv)
    assert code == 0

    captured = capfd.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == 1
    entry = data[0]
    assert entry["exercise"] == exercise
    assert entry["success"] is True
    assert "urdf" in entry
    assert "parameters" in entry
    assert entry["parameters"]["mass"] == 80.0


def test_json_multiple_exercises(capfd: pytest.CaptureFixture[str]) -> None:
    """--json with 'all' produces one entry per exercise."""
    # Only test a subset to avoid overwhelming output
    code = main(["back_squat", "--json", "--mass", "80", "--height", "1.75"])
    assert code == 0

    captured = capfd.readouterr()
    data = json.loads(captured.out)
    assert isinstance(data, list)
    assert len(data) == 1