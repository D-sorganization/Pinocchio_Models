"""Tests for Gepetto-viewer addon (mocked — no real gepetto dependency)."""

from unittest.mock import patch

import pytest

from pinocchio_models.shared.barbell import BarbellSpec


class TestGepettoViewerImportGuard:
    def test_raises_import_error_without_gepetto(self):
        with patch.dict("sys.modules", {"pinocchio": None}):
            # Re-import to trigger the guard
            import importlib

            import pinocchio_models.addons.gepetto.viewer as viewer_mod

            importlib.reload(viewer_mod)

            with pytest.raises(ImportError, match="Gepetto-viewer is not installed"):
                viewer_mod.create_viewer("test", "<robot/>")

    def test_display_configuration_raises_without_gepetto(self):
        with patch.dict("sys.modules", {"pinocchio": None}):
            import importlib

            import pinocchio_models.addons.gepetto.viewer as viewer_mod

            importlib.reload(viewer_mod)

            with pytest.raises(ImportError, match="Gepetto-viewer is not installed"):
                viewer_mod.display_configuration(None, None)

    def test_add_barbell_visual_raises_without_gepetto(self):
        with patch.dict("sys.modules", {"pinocchio": None}):
            import importlib

            import pinocchio_models.addons.gepetto.viewer as viewer_mod

            importlib.reload(viewer_mod)

            spec = BarbellSpec.mens_olympic()
            with pytest.raises(ImportError, match="Gepetto-viewer is not installed"):
                viewer_mod.add_barbell_visual(None, spec)
