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
        with patch.dict("sys.modules", {"crocoddyl": None, "pinocchio": None}):
            import importlib

            import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

            importlib.reload(oc_mod)

            # Import guard fires before validation, but validation
            # function can be tested directly
            with pytest.raises(ValueError, match="Unknown exercise"):
                oc_mod._validate_exercise_name("not_a_real_exercise")


class TestExerciseNameValidation:
    def test_rejects_invalid_exercise_name(self) -> None:
        """Validates exercise name even when crocoddyl is missing."""
        with patch.dict("sys.modules", {"crocoddyl": None, "pinocchio": None}):
            import importlib

            import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

            importlib.reload(oc_mod)

            # The import guard fires before validation, so we test
            # the validation function directly
            with pytest.raises(ValueError, match="Unknown exercise"):
                oc_mod._validate_exercise_name("invalid_exercise")

    def test_accepts_valid_exercise_names(self) -> None:
        import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

        for name in (
            "back_squat",
            "bench_press",
            "deadlift",
            "snatch",
            "clean_and_jerk",
            "gait",
            "sit_to_stand",
        ):
            oc_mod._validate_exercise_name(name)


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
