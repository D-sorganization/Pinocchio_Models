"""Tests for the CLI entry point."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest

from pinocchio_models.__main__ import (
    _build_urdf_for,
    _emit_urdf,
    _selected_exercises,
    main,
)


class TestCLI:
    def test_generates_single_exercise_to_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(["back_squat", "--output-dir", tmpdir])
            assert result == 0
            urdf_path = Path(tmpdir) / "back_squat.urdf"
            assert urdf_path.exists()
            content = urdf_path.read_text()
            assert "<robot" in content
            assert 'name="back_squat"' in content

    def test_generates_all_exercises_to_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(["all", "--output-dir", tmpdir])
            assert result == 0
            files = list(Path(tmpdir).glob("*.urdf"))
            assert len(files) == 7

    def test_generates_with_custom_parameters(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            result = main(
                [
                    "bench_press",
                    "--mass",
                    "90",
                    "--height",
                    "1.80",
                    "--plates",
                    "60",
                    "--output-dir",
                    tmpdir,
                ]
            )
            assert result == 0
            assert (Path(tmpdir) / "bench_press.urdf").exists()

    def test_generates_to_stdout(self, capsys: object) -> None:
        """When no --output-dir, output goes to stdout."""
        result = main(["deadlift"])
        assert result == 0


class TestValidateCliArgs:
    def test_rejects_non_positive_mass(self) -> None:
        with pytest.raises(SystemExit):
            main(["back_squat", "--mass", "0", "--output-dir", "."])

    def test_accepts_valid_args(self) -> None:
        # Smoke-test through main; non-positive mass would have raised SystemExit.
        with tempfile.TemporaryDirectory() as tmpdir:
            assert main(["back_squat", "--mass", "70", "--output-dir", tmpdir]) == 0


class TestEmitUrdf:
    def test_writes_urdf_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            out_dir = Path(tmpdir) / "models"
            _emit_urdf("back_squat", '<robot name="r"/>', out_dir)
            urdf_path = out_dir / "back_squat.urdf"
            assert urdf_path.exists()
            assert "robot" in urdf_path.read_text()

    def test_stdout_when_output_dir_is_none(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        _emit_urdf("squat", '<robot name="r"/>', None)
        captured = capsys.readouterr()
        assert "<robot" in captured.out


class TestCliHelpers:
    def test_selected_exercises_expands_all(self) -> None:
        exercises = _selected_exercises("all")
        assert "back_squat" in exercises
        assert "bench_press" in exercises

    def test_selected_exercises_keeps_single_name(self) -> None:
        assert _selected_exercises("deadlift") == ["deadlift"]

    def test_build_urdf_for_returns_robot_xml(self) -> None:
        urdf = _build_urdf_for(
            "back_squat",
            body_mass=80.0,
            height=1.75,
            plate_mass_per_side=0.0,
        )
        assert "<robot" in urdf
