"""Tests for Gepetto-viewer addon (mocked -- no real gepetto dependency)."""

from unittest.mock import MagicMock, patch

import pytest

from pinocchio_models.shared.barbell import BarbellSpec


class TestGepettoViewerImportGuard:
    def test_raises_import_error_without_gepetto(self) -> None:
        with patch.dict("sys.modules", {"pinocchio": None}):
            # Re-import to trigger the guard
            import importlib

            import pinocchio_models.addons.gepetto.viewer as viewer_mod

            importlib.reload(viewer_mod)

            with pytest.raises(ImportError, match="Gepetto-viewer is not installed"):
                viewer_mod.create_viewer("test", "<robot/>")

    def test_display_configuration_raises_without_gepetto(self) -> None:
        with patch.dict("sys.modules", {"pinocchio": None}):
            import importlib

            import pinocchio_models.addons.gepetto.viewer as viewer_mod

            importlib.reload(viewer_mod)

            with pytest.raises(ImportError, match="Gepetto-viewer is not installed"):
                viewer_mod.display_configuration(None, None)

    def test_add_barbell_visual_raises_without_gepetto(self) -> None:
        with patch.dict("sys.modules", {"pinocchio": None}):
            import importlib

            import pinocchio_models.addons.gepetto.viewer as viewer_mod

            importlib.reload(viewer_mod)

            spec = BarbellSpec.mens_olympic()
            with pytest.raises(ImportError, match="Gepetto-viewer is not installed"):
                viewer_mod.add_barbell_visual(None, spec)


class TestExerciseNameValidation:
    def test_rejects_invalid_exercise_name(self) -> None:
        import pinocchio_models.addons.gepetto.viewer as viewer_mod

        with pytest.raises(ValueError, match="Unknown exercise"):
            viewer_mod._validate_exercise_name("not_an_exercise")

    def test_accepts_valid_exercise_names(self) -> None:
        import pinocchio_models.addons.gepetto.viewer as viewer_mod

        for name in (
            "back_squat",
            "bench_press",
            "deadlift",
            "snatch",
            "clean_and_jerk",
        ):
            viewer_mod._validate_exercise_name(name)


class TestCreateViewerWithMock:
    def test_create_viewer_calls_pinocchio(self) -> None:
        """Verify create_viewer wires up pinocchio model building correctly."""
        mock_pin = MagicMock()
        mock_pin.JointModelFreeFlyer.return_value = MagicMock()
        mock_model = MagicMock()
        mock_pin.buildModelFromXML.return_value = mock_model
        mock_pin.buildGeomFromModelAndXML.return_value = MagicMock()
        mock_pin.GeometryType.VISUAL = "VISUAL"
        mock_model.createData.return_value = MagicMock()

        mock_viz_class = MagicMock()
        mock_viewer_instance = MagicMock()
        mock_viz_class.return_value = mock_viewer_instance

        with patch.dict("sys.modules", {"pinocchio": mock_pin}):
            import importlib

            import pinocchio_models.addons.gepetto.viewer as viewer_mod

            importlib.reload(viewer_mod)
            viewer_mod.GepettoVisualizer = mock_viz_class
            viewer_mod._HAS_GEPETTO = True

            result = viewer_mod.create_viewer("test_model", "<robot/>")

            mock_pin.buildModelFromXML.assert_called_once()
            mock_viewer_instance.initViewer.assert_called_once()
            assert result is mock_viewer_instance


class TestDisplayConfiguration:
    def test_display_calls_viewer_display(self) -> None:
        """Verify display_configuration calls viewer.display."""
        import pinocchio_models.addons.gepetto.viewer as viewer_mod

        original = viewer_mod._HAS_GEPETTO
        viewer_mod._HAS_GEPETTO = True
        try:
            mock_viewer = MagicMock()
            viewer_mod.display_configuration(mock_viewer, [0, 0, 0])
            mock_viewer.display.assert_called_once_with([0, 0, 0])
        finally:
            viewer_mod._HAS_GEPETTO = original
