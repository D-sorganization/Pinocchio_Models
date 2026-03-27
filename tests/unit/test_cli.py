"""Tests for the CLI entry point."""

from __future__ import annotations

import tempfile
from pathlib import Path

from pinocchio_models.__main__ import main


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
