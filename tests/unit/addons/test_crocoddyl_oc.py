"""Tests for Crocoddyl optimal control addon (mocked -- no real dependency)."""

from unittest.mock import MagicMock, patch

import numpy as np
import pytest


class TestCrocoddylOCImportGuard:
    def test_raises_import_error_without_crocoddyl(self) -> None:
        with patch.dict("sys.modules", {"crocoddyl": None, "pinocchio": None}):
            import importlib

            import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

            importlib.reload(oc_mod)

            with pytest.raises(ImportError, match="Crocoddyl is not installed"):
                oc_mod.create_exercise_ocp("<robot/>", "back_squat")

    def test_solve_trajectory_raises_without_crocoddyl(self) -> None:
        with patch.dict("sys.modules", {"crocoddyl": None, "pinocchio": None}):
            import importlib

            import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

            importlib.reload(oc_mod)

            with pytest.raises(ImportError, match="Crocoddyl is not installed"):
                oc_mod.solve_trajectory(None)  # type: ignore

    def test_extract_torques_raises_without_crocoddyl(self) -> None:
        with patch.dict("sys.modules", {"crocoddyl": None, "pinocchio": None}):
            import importlib

            import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

            importlib.reload(oc_mod)

            with pytest.raises(ImportError, match="Crocoddyl is not installed"):
                oc_mod.extract_joint_torques(([], []), None)  # type: ignore


class TestCyclicOCPImportGuard:
    def test_cyclic_ocp_raises_without_crocoddyl(self) -> None:
        with patch.dict("sys.modules", {"crocoddyl": None, "pinocchio": None}):
            import importlib

            import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

            importlib.reload(oc_mod)

            with pytest.raises(ImportError, match="Crocoddyl is not installed"):
                oc_mod.create_cyclic_ocp("<robot/>", "gait")

    def test_cyclic_ocp_validates_exercise_name(self) -> None:
        from pinocchio_models.shared.contracts.preconditions import (
            require_valid_exercise_name,
        )

        # Validation function is now in shared preconditions
        with pytest.raises(ValueError, match="Unknown exercise"):
            require_valid_exercise_name("not_a_real_exercise")


class TestExerciseNameValidation:
    def test_rejects_invalid_exercise_name(self) -> None:
        """Validates exercise name via shared preconditions."""
        from pinocchio_models.shared.contracts.preconditions import (
            require_valid_exercise_name,
        )

        with pytest.raises(ValueError, match="Unknown exercise"):
            require_valid_exercise_name("invalid_exercise")

    def test_accepts_valid_exercise_names(self) -> None:
        from pinocchio_models.shared.contracts.preconditions import (
            require_valid_exercise_name,
        )

        for name in (
            "back_squat",
            "bench_press",
            "deadlift",
            "snatch",
            "clean_and_jerk",
            "gait",
            "sit_to_stand",
        ):
            require_valid_exercise_name(name)


class TestExtractJointTorques:
    def test_extracts_controls_from_trajectory(self) -> None:
        """extract_joint_torques should use controls from trajectory, not re-solve."""
        import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

        # Mock _HAS_CROCODDYL to True
        original = oc_mod._HAS_CROCODDYL
        oc_mod._HAS_CROCODDYL = True
        try:
            mock_ocp = MagicMock()
            states = [np.zeros(10) for _ in range(5)]
            controls = [np.ones(3) * i for i in range(4)]
            trajectory = (states, controls)

            result = oc_mod.extract_joint_torques(trajectory, mock_ocp)
            np.testing.assert_array_equal(result, np.array(controls))
        finally:
            oc_mod._HAS_CROCODDYL = original


class TestSolveTrajectoryDbCContracts:
    """DbC contracts for solve_trajectory (issue #124)."""

    def test_rejects_non_finite_initial_state(self) -> None:
        """initial_state must be finite."""
        import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

        original = oc_mod._HAS_CROCODDYL
        oc_mod._HAS_CROCODDYL = True
        try:
            mock_ocp = MagicMock()
            bad_state = np.array([float("nan"), 1.0, 2.0])
            with pytest.raises(ValueError, match="initial_state.*non-finite"):
                oc_mod.solve_trajectory(mock_ocp, initial_state=bad_state)
        finally:
            oc_mod._HAS_CROCODDYL = original

    def test_rejects_inf_initial_state(self) -> None:
        """initial_state must not contain Inf."""
        import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

        original = oc_mod._HAS_CROCODDYL
        oc_mod._HAS_CROCODDYL = True
        try:
            mock_ocp = MagicMock()
            bad_state = np.array([float("inf"), 1.0, 2.0])
            with pytest.raises(ValueError, match="initial_state.*non-finite"):
                oc_mod.solve_trajectory(mock_ocp, initial_state=bad_state)
        finally:
            oc_mod._HAS_CROCODDYL = original

    def test_accepts_valid_initial_state(self) -> None:
        """solve_trajectory should proceed normally with a valid finite initial state."""
        import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

        original_flag = oc_mod._HAS_CROCODDYL
        original_cro = getattr(oc_mod, "crocoddyl", None)
        oc_mod._HAS_CROCODDYL = True
        mock_cro = MagicMock()
        mock_solver = MagicMock()
        mock_solver.xs = [np.zeros(10)]
        mock_solver.us = [np.zeros(3)]
        mock_cro.SolverDDP.return_value = mock_solver
        oc_mod.crocoddyl = mock_cro
        try:
            mock_ocp = MagicMock()
            valid_state = np.zeros(10)
            states, controls = oc_mod.solve_trajectory(
                mock_ocp, initial_state=valid_state
            )
            assert len(states) == 1
            assert len(controls) == 1
        finally:
            oc_mod._HAS_CROCODDYL = original_flag
            if original_cro is None:
                del oc_mod.crocoddyl
            else:
                oc_mod.crocoddyl = original_cro
