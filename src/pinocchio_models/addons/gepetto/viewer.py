"""Gepetto-viewer integration for visualizing Pinocchio models.

Provides a thin wrapper around gepetto.corbaserver for rendering
exercise models. Gracefully degrades if gepetto is not installed.

Usage requires the optional ``gepetto`` extra::

    pip install pinocchio-models[gepetto]
"""

from __future__ import annotations

from typing import Any

try:
    import pinocchio as pin
    from pinocchio.visualize import GepettoVisualizer

    _HAS_GEPETTO = True
except ImportError:
    _HAS_GEPETTO = False

from pinocchio_models.shared.barbell import BarbellSpec


def _require_gepetto() -> None:
    """Raise ImportError with installation instructions if gepetto is missing."""
    if not _HAS_GEPETTO:
        raise ImportError(
            "Gepetto-viewer is not installed. "
            "Install with: pip install pinocchio-models[gepetto]"
        )


def create_viewer(model_name: str, urdf_str: str) -> Any:
    """Create a Gepetto viewer for a Pinocchio model.

    Parameters
    ----------
    model_name : str
        Name displayed in the viewer window.
    urdf_str : str
        URDF XML string of the model.

    Returns
    -------
    GepettoVisualizer or None
        Viewer handle, or None if gepetto is unavailable.
    """
    _require_gepetto()

    model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
    visual_model = pin.buildGeomFromModelAndXML(
        model, urdf_str, pin.GeometryType.VISUAL
    )
    data = model.createData()

    viewer = GepettoVisualizer(model, data, visual_model)
    viewer.initViewer(windowName=model_name)
    viewer.loadViewerModel(rootNodeName=model_name)

    return viewer


def display_configuration(viewer: Any, q: Any) -> None:
    """Display a joint configuration in the viewer.

    Parameters
    ----------
    viewer : GepettoVisualizer
        Viewer handle from create_viewer().
    q : array-like
        Joint configuration vector (nq,).
    """
    _require_gepetto()
    viewer.display(q)


def add_barbell_visual(viewer: Any, spec: BarbellSpec) -> None:
    """Add visual markers for barbell dimensions to the viewer.

    Parameters
    ----------
    viewer : GepettoVisualizer
        Viewer handle from create_viewer().
    spec : BarbellSpec
        Barbell specification for dimensions.
    """
    _require_gepetto()

    gui = viewer.viewer.gui
    scene = viewer.viewerRootNodeName

    shaft_name = f"{scene}/barbell_shaft_marker"
    gui.addCylinder(
        shaft_name,
        spec.shaft_radius,
        spec.shaft_length,
        [0.6, 0.6, 0.6, 1.0],
    )

    for side, _sign in [("left", -1.0), ("right", 1.0)]:
        sleeve_name = f"{scene}/barbell_{side}_sleeve_marker"
        gui.addCylinder(
            sleeve_name,
            spec.sleeve_radius,
            spec.sleeve_length,
            [0.3, 0.3, 0.3, 1.0],
        )
