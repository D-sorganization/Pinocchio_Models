"""Tests for Pink IK addon (mocked — no real pink dependency)."""

from unittest.mock import patch

import pytest


class TestPinkIKImportGuard:
    def test_raises_import_error_without_pink(self):
        with patch.dict("sys.modules", {"pinocchio": None, "pink": None}):
            import importlib

            import pinocchio_models.addons.pink.ik_solver as ik_mod

            importlib.reload(ik_mod)

            with pytest.raises(ImportError, match="Pink is not installed"):
                ik_mod.create_ik_problem("<robot/>", ["frame1"])

    def test_solve_pose_raises_without_pink(self):
        with patch.dict("sys.modules", {"pinocchio": None, "pink": None}):
            import importlib

            import pinocchio_models.addons.pink.ik_solver as ik_mod

            importlib.reload(ik_mod)

            with pytest.raises(ImportError, match="Pink is not installed"):
                ik_mod.solve_pose(None, {})

    def test_compute_keyframes_raises_without_pink(self):
        with patch.dict("sys.modules", {"pinocchio": None, "pink": None}):
            import importlib

            import pinocchio_models.addons.pink.ik_solver as ik_mod

            importlib.reload(ik_mod)

            with pytest.raises(ImportError, match="Pink is not installed"):
                ik_mod.compute_exercise_keyframes("<robot/>", "squat")
