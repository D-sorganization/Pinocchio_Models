"""Tests for Crocoddyl optimal control addon (mocked — no real dependency)."""

from unittest.mock import patch

import pytest


class TestCrocoddylOCImportGuard:
    def test_raises_import_error_without_crocoddyl(self):
        with patch.dict("sys.modules", {"crocoddyl": None, "pinocchio": None}):
            import importlib

            import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

            importlib.reload(oc_mod)

            with pytest.raises(ImportError, match="Crocoddyl is not installed"):
                oc_mod.create_exercise_ocp("<robot/>", "squat")

    def test_solve_trajectory_raises_without_crocoddyl(self):
        with patch.dict("sys.modules", {"crocoddyl": None, "pinocchio": None}):
            import importlib

            import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

            importlib.reload(oc_mod)

            with pytest.raises(ImportError, match="Crocoddyl is not installed"):
                oc_mod.solve_trajectory(None)

    def test_extract_torques_raises_without_crocoddyl(self):
        with patch.dict("sys.modules", {"crocoddyl": None, "pinocchio": None}):
            import importlib

            import pinocchio_models.addons.crocoddyl.optimal_control as oc_mod

            importlib.reload(oc_mod)

            with pytest.raises(ImportError, match="Crocoddyl is not installed"):
                oc_mod.extract_joint_torques([], None)
