"""Tests for the model-pack manifest and launcher entry point.

Mirrors the MuJoCo coordination test shape (see UpstreamDrift #5179 /
#5184). The live-pinocchio assertions are marked ``live_simulation``
so they are skipped in default CI but exercised on rigs with the real
``pin`` package available.
"""

from __future__ import annotations

import importlib
import subprocess
import sys
import tempfile
import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
import yaml

from pinocchio_models import model_pack

# Exercises that require Pinocchio's floating base via
# ``pin.JointModelFreeFlyer()``. Per repo CLAUDE.md, every exercise in
# this package uses the free-flyer floating base; this set documents
# the contract for the launcher integration.
_FLOATING_BASE_EXERCISES: frozenset[str] = frozenset(
    {
        "squat",
        "deadlift",
        "bench_press",
        "snatch",
        "clean_and_jerk",
        "gait",
        "sit_to_stand",
    }
)

_EXPECTED_EXERCISE_IDS: tuple[str, ...] = (
    "squat",
    "deadlift",
    "bench_press",
    "snatch",
    "clean_and_jerk",
    "gait",
    "sit_to_stand",
)


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


class TestManifest:
    def test_manifest_returns_mapping(self) -> None:
        data = model_pack.manifest()
        assert isinstance(data, dict)

    def test_schema_is_model_pack_v1(self) -> None:
        assert model_pack.manifest()["schema"] == "model_pack/v1"

    def test_engine_metadata(self) -> None:
        data = model_pack.manifest()
        assert data["engine"] == "pinocchio"
        assert data["engine_version"] == ">=2.7"
        assert data["format"] == "urdf"
        assert data["anthropometrics"] == "winter_2009"

    def test_addons_block_present(self) -> None:
        data = model_pack.manifest()
        addons = data.get("addons")
        assert isinstance(addons, dict)
        for name in ("gepetto", "pink", "crocoddyl"):
            assert addons.get(name) == "optional"

    def test_repo_root_yaml_matches_loaded_manifest(self) -> None:
        on_disk = yaml.safe_load(
            (_repo_root() / "model_pack.yaml").read_text(encoding="utf-8")
        )
        assert model_pack.manifest() == on_disk


class TestListExercises:
    def test_returns_expected_ids_in_order(self) -> None:
        assert model_pack.list_exercises() == list(_EXPECTED_EXERCISE_IDS)

    def test_all_ids_are_floating_base_exercises(self) -> None:
        for exercise_id in model_pack.list_exercises():
            assert exercise_id in _FLOATING_BASE_EXERCISES


class TestResolve:
    def test_resolve_returns_existing_directory(self) -> None:
        root = model_pack.resolve()
        assert root.is_dir(), f"{root} does not exist"

    def test_resolve_contains_each_declared_exercise(self) -> None:
        root = model_pack.resolve()
        for exercise_id in _EXPECTED_EXERCISE_IDS:
            assert (root / exercise_id).is_dir(), (
                f"missing exercise directory: {exercise_id}"
            )


class TestEntryPointDiscoverable:
    """The biomech.model_pack entry point must be discoverable by importers."""

    def test_module_exposes_required_callables(self) -> None:
        mod = importlib.import_module("pinocchio_models.model_pack")
        for attr in ("resolve", "manifest", "list_exercises"):
            assert callable(getattr(mod, attr))


class TestLauncherCLI:
    def test_list_exercises_flag_prints_ids(self) -> None:
        result = subprocess.run(
            [sys.executable, "-m", "pinocchio_models", "--list-exercises"],
            capture_output=True,
            text=True,
            check=False,
        )
        assert result.returncode == 0, result.stderr
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        assert lines == list(_EXPECTED_EXERCISE_IDS)

    @pytest.mark.parametrize("exercise_id", _EXPECTED_EXERCISE_IDS)
    def test_export_writes_valid_urdf(self, exercise_id: str) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / f"{exercise_id}.urdf"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pinocchio_models",
                    "--exercise",
                    exercise_id,
                    "--export",
                    str(export_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, result.stderr
            assert export_path.exists()
            root = ET.fromstring(export_path.read_text(encoding="utf-8"))
            assert root.tag == "robot"
            # Every exercise has at least one link and one joint.
            assert len(root.findall("link")) > 0
            assert len(root.findall("joint")) > 0


@pytest.mark.live_simulation
class TestPinocchioParse:
    """Live-simulation tests: require the real ``pin`` package.

    These tests use ``pinocchio.buildModelFromUrdf`` per the issue
    contract. They are skipped in default CI and run only on rigs with
    Pinocchio installed.
    """

    @pytest.mark.parametrize("exercise_id", _EXPECTED_EXERCISE_IDS)
    def test_parse_via_build_model_from_urdf(self, exercise_id: str) -> None:
        pin = pytest.importorskip("pinocchio", reason="pin package not installed")
        if not hasattr(pin, "buildModelFromUrdf"):
            pytest.skip("pin.buildModelFromUrdf not available in this build")

        with tempfile.TemporaryDirectory() as tmpdir:
            export_path = Path(tmpdir) / f"{exercise_id}.urdf"
            result = subprocess.run(
                [
                    sys.executable,
                    "-m",
                    "pinocchio_models",
                    "--exercise",
                    exercise_id,
                    "--export",
                    str(export_path),
                ],
                capture_output=True,
                text=True,
                check=False,
            )
            assert result.returncode == 0, result.stderr

            # Build with the free-flyer floating base where required.
            if exercise_id in _FLOATING_BASE_EXERCISES:
                model = pin.buildModelFromUrdf(
                    str(export_path), pin.JointModelFreeFlyer()
                )
                # nq must include the 7-DOF floating base (3 trans + 4 quat).
                assert model.nq >= 7
            else:
                model = pin.buildModelFromUrdf(str(export_path))
                assert model.nq > 0
