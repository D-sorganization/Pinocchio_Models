"""Tests for Pink IK addon (mocked -- no real pink dependency)."""

from unittest.mock import patch

import pytest

from pinocchio_models.shared.contracts.preconditions import (
    require_valid_exercise_name,
)


class TestPinkIKImportGuard:
    def test_raises_import_error_without_pink(self) -> None:
        with patch.dict("sys.modules", {"pinocchio": None, "pink": None}):
            import importlib

            import pinocchio_models.addons.pink.ik_solver as ik_mod

            importlib.reload(ik_mod)

            with pytest.raises(ImportError, match="Pink is not installed"):
                ik_mod.create_ik_problem('<robot name="t"/>', ["frame1"])

    def test_solve_pose_raises_without_pink(self) -> None:
        with patch.dict("sys.modules", {"pinocchio": None, "pink": None}):
            import importlib

            import pinocchio_models.addons.pink.ik_solver as ik_mod

            importlib.reload(ik_mod)

            with pytest.raises(ImportError, match="Pink is not installed"):
                ik_mod.solve_pose(None, {})  # type: ignore[arg-type]

    def test_compute_keyframes_raises_without_pink(self) -> None:
        with patch.dict("sys.modules", {"pinocchio": None, "pink": None}):
            import importlib

            import pinocchio_models.addons.pink.ik_solver as ik_mod

            importlib.reload(ik_mod)

            with pytest.raises(ImportError, match="Pink is not installed"):
                ik_mod.compute_exercise_keyframes('<robot name="t"/>', "back_squat")


class TestExerciseNameValidation:
    """Exercise name validation uses the shared precondition (DRY, issue #79)."""

    def test_rejects_invalid_exercise_name(self) -> None:
        with pytest.raises(ValueError, match="Unknown exercise"):
            require_valid_exercise_name("invalid_exercise")

    def test_accepts_valid_exercise_names(self) -> None:
        for name in (
            "back_squat",
            "bench_press",
            "deadlift",
            "snatch",
            "clean_and_jerk",
        ):
            require_valid_exercise_name(name)


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


class TestUrdfValidation:
    """URDF string validation before Pinocchio dispatch (issue #55)."""

    def test_create_ik_problem_rejects_empty_urdf(self) -> None:
        with patch.dict("sys.modules", {"pinocchio": None, "pink": None}):
            import importlib

            import pinocchio_models.addons.pink.ik_solver as ik_mod

            importlib.reload(ik_mod)
            ik_mod._HAS_PINK = True

            with pytest.raises(ValueError, match="must not be empty"):
                ik_mod.create_ik_problem("", ["frame1"])


class TestSolvePoseDbCContracts:
    """DbC contracts for solve_pose (issue #124)."""

    def test_rejects_non_matrix_target_pose(self) -> None:
        """targets values must be (4,4) SE(3) matrices."""
        import importlib

        import numpy as np

        import pinocchio_models.addons.pink.ik_solver as ik_mod

        importlib.reload(ik_mod)
        ik_mod._HAS_PINK = True

        from unittest.mock import MagicMock

        mock_problem = MagicMock()
        bad_targets = {"frame1": np.zeros((3, 4))}  # wrong shape

        with pytest.raises(ValueError, match="SE\\(3\\) pose.*must be a \\(4, 4\\)"):
            ik_mod.solve_pose(mock_problem, bad_targets)

    def test_rejects_non_finite_target_pose(self) -> None:
        """targets values must be finite."""
        import importlib

        import numpy as np

        import pinocchio_models.addons.pink.ik_solver as ik_mod

        importlib.reload(ik_mod)
        ik_mod._HAS_PINK = True

        from unittest.mock import MagicMock

        mock_problem = MagicMock()
        nan_pose = np.eye(4)
        nan_pose[0, 0] = float("nan")
        bad_targets = {"frame1": nan_pose}

        with pytest.raises(ValueError, match="SE\\(3\\) pose.*non-finite"):
            ik_mod.solve_pose(mock_problem, bad_targets)

    def test_warns_when_ik_does_not_converge(self) -> None:
        """solve_pose should warn when max_iterations exhausted without convergence."""
        import importlib

        import numpy as np

        import pinocchio_models.addons.pink.ik_solver as ik_mod
        from unittest.mock import MagicMock, patch

        importlib.reload(ik_mod)
        ik_mod._HAS_PINK = True

        mock_pin = MagicMock()
        mock_pin.neutral.return_value = np.zeros(7)
        mock_pink_lib = MagicMock()
        mock_configuration = MagicMock()
        mock_configuration.q = np.zeros(7)
        mock_pink_lib.Configuration.return_value = mock_configuration

        ik_mod.pin = mock_pin
        ik_mod.pink = mock_pink_lib

        mock_problem = MagicMock()
        mock_problem.model = MagicMock()
        mock_problem.data = MagicMock()
        targets = {"frame1": np.eye(4)}

        with patch.object(ik_mod, "_build_target_tasks", return_value=[MagicMock()]):
            with patch.object(ik_mod, "_ik_step", return_value=mock_configuration):
                with patch.object(ik_mod, "_check_convergence", return_value=False):
                    with pytest.warns(UserWarning, match="IK did not converge"):
                        ik_mod.solve_pose(
                            mock_problem, targets, max_iterations=5
                        )
