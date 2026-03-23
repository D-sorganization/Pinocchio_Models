"""Tests for Pink IK addon (mocked -- no real pink dependency)."""

from unittest.mock import patch

import pytest


class TestPinkIKImportGuard:
    def test_raises_import_error_without_pink(self) -> None:
        with patch.dict("sys.modules", {"pinocchio": None, "pink": None}):
            import importlib

            import pinocchio_models.addons.pink.ik_solver as ik_mod

            importlib.reload(ik_mod)

            with pytest.raises(ImportError, match="Pink is not installed"):
                ik_mod.create_ik_problem("<robot/>", ["frame1"])

    def test_solve_pose_raises_without_pink(self) -> None:
        with patch.dict("sys.modules", {"pinocchio": None, "pink": None}):
            import importlib

            import pinocchio_models.addons.pink.ik_solver as ik_mod

            importlib.reload(ik_mod)

            with pytest.raises(ImportError, match="Pink is not installed"):
                ik_mod.solve_pose(None, {})

    def test_compute_keyframes_raises_without_pink(self) -> None:
        with patch.dict("sys.modules", {"pinocchio": None, "pink": None}):
            import importlib

            import pinocchio_models.addons.pink.ik_solver as ik_mod

            importlib.reload(ik_mod)

            with pytest.raises(ImportError, match="Pink is not installed"):
                ik_mod.compute_exercise_keyframes("<robot/>", "back_squat")


class TestExerciseNameValidation:
    def test_rejects_invalid_exercise_name(self) -> None:
        import pinocchio_models.addons.pink.ik_solver as ik_mod

        with pytest.raises(ValueError, match="Unknown exercise"):
            ik_mod._validate_exercise_name("invalid_exercise")

    def test_accepts_valid_exercise_names(self) -> None:
        import pinocchio_models.addons.pink.ik_solver as ik_mod

        for name in (
            "back_squat",
            "bench_press",
            "deadlift",
            "snatch",
            "clean_and_jerk",
        ):
            ik_mod._validate_exercise_name(name)


class TestExercisePhases:
    def test_all_exercises_have_phases(self) -> None:
        import pinocchio_models.addons.pink.ik_solver as ik_mod

        for name in (
            "back_squat",
            "bench_press",
            "deadlift",
            "snatch",
            "clean_and_jerk",
        ):
            phases = ik_mod._EXERCISE_PHASES.get(name, [])
            assert len(phases) >= 3, f"{name} should have at least 3 phases"

    def test_phase_fractions_in_range(self) -> None:
        import pinocchio_models.addons.pink.ik_solver as ik_mod

        for name, phases in ik_mod._EXERCISE_PHASES.items():
            for phase_name, fraction in phases:
                assert 0.0 <= fraction <= 1.0, (
                    f"{name}/{phase_name} fraction {fraction} out of range"
                )
