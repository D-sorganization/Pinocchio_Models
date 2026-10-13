"""Headless recording of an exercise rollout as a Meshcat animation (#438).

:func:`record_rollout` replays a configuration trajectory on an exercise
model with :class:`pinocchio.visualize.MeshcatVisualizer` and writes the
result as a **self-contained static HTML file**: the Meshcat scene (the
model's visual geometry) plus a keyframed animation clip with one keyframe
per configuration. Opening the file in any browser plays the rollout; no
server is needed afterwards.

The recording is headless:

* a private Meshcat server is started on ``127.0.0.1`` only for the duration
  of the call and is always shut down before returning (also on error);
* no browser and no GUI window is ever opened.

The artifact is an HTML animation, not an encoded video file (MP4/WebM);
producing pixels would need a browser or an offscreen renderer.

The rollout is engine-agnostic input: either a sequence of configurations
(a kinematic replay, e.g. interpolated exercise keyframes) or a callable that
receives the resolved ``pinocchio.Model`` and returns the configurations (for
example a forward-dynamics simulation), so any trajectory producer can feed
the recorder.

Requires the optional ``meshcat`` extra::

    pip install pinocchio-models[meshcat]
"""

from __future__ import annotations

import base64
import binascii
import re
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
from numpy.typing import ArrayLike

from robotics_contracts.preconditions import (
    require_finite,
    require_positive,
    require_shape,
)

Rollout = Sequence[ArrayLike] | Callable[[Any], Iterable[ArrayLike]]
"""Configurations to record, or a callable ``model -> configurations``."""

_RECORDING_SUFFIX = ".html"
_COMMAND_BLOB = re.compile(r"data:application/octet-binary;base64,([A-Za-z0-9+/=]+)")


@dataclass(frozen=True)
class RolloutRecording:
    """Result of :func:`record_rollout`.

    Attributes:
        path: The written self-contained HTML file.
        frame_count: Number of animation keyframes (one per configuration).
        fps: Playback rate of the animation in whole frames per second.
        size_bytes: Size of the written file.
    """

    path: Path
    frame_count: int
    fps: int
    size_bytes: int

    @property
    def duration_s(self) -> float:
        """Playback duration of the animation in seconds."""
        return self.frame_count / self.fps


def record_rollout(
    exercise: str,
    rollout: Rollout,
    output_path: str | Path,
    *,
    fps: int = 30,
) -> RolloutRecording:
    """Record an exercise rollout headlessly as a Meshcat HTML animation.

    Args:
        exercise: Manifest exercise id (e.g. ``"squat"``). The URDF is needed
            for the visual geometry, so a bare ``pinocchio.Model`` is not
            accepted.
        rollout: Sequence of configurations, each shape ``(model.nq,)``, or a
            callable receiving the ``pinocchio.Model`` and returning them.
        output_path: Destination file; must end in ``.html`` and its parent
            directory must exist. An existing file is overwritten.
        fps: Playback rate in whole frames per second (> 0); Meshcat animation
            clips store an integer rate.

    Returns:
        A :class:`RolloutRecording` describing the written artifact.

    Raises:
        ValueError: Unknown exercise, empty rollout, wrong configuration
            shape, non-finite values, bad ``fps`` or bad ``output_path``.
        ImportError: ``meshcat`` is not installed.
        RuntimeError: The written file does not contain the expected
            animation (postcondition).
    """
    require_positive(fps, "fps")
    if int(fps) != fps:
        raise ValueError(f"fps must be a whole number, got {fps}")
    path = _require_output_path(output_path)

    from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

    urdf = build_urdf(exercise)
    model = load_model(urdf)
    frames = _require_configurations(rollout, model)

    html = _render_animation_html(model, urdf, frames, fps)
    path.write_text(html, encoding="utf-8")

    recording = RolloutRecording(
        path=path,
        frame_count=len(frames),
        fps=int(fps),
        size_bytes=path.stat().st_size,
    )
    _ensure_recording(recording)
    return recording


def recorded_frame_count(path: str | Path) -> int:
    """Return the number of animation keyframes stored in a recording.

    Decodes the Meshcat commands embedded in a file written by
    :func:`record_rollout` and counts the keyframes of its animation clips.

    Raises:
        ValueError: The file holds no animation or its clips disagree on the
            number of keyframes.
    """
    import umsgpack  # ships with meshcat

    counts: set[int] = set()
    html = Path(path).read_text(encoding="utf-8")
    for blob in _COMMAND_BLOB.findall(html):
        try:
            command = umsgpack.unpackb(base64.b64decode(blob))
        except (binascii.Error, umsgpack.UnpackException):
            continue
        if isinstance(command, dict) and command.get("type") == "set_animation":
            for entry in command["animations"]:
                counts.update(len(t["keys"]) for t in entry["clip"]["tracks"])
    if len(counts) != 1:
        raise ValueError(
            f"{path}: expected one consistent animation, found keyframe "
            f"counts {sorted(counts)}"
        )
    return counts.pop()


def _require_output_path(output_path: str | Path) -> Path:
    path = Path(output_path)
    if path.suffix.lower() != _RECORDING_SUFFIX:
        raise ValueError(
            f"output_path must end in {_RECORDING_SUFFIX!r}, got {str(path)!r}"
        )
    if not path.parent.is_dir():
        raise ValueError(f"output_path directory does not exist: {path.parent}")
    return path


def _require_configurations(rollout: Rollout, model: Any) -> list[np.ndarray]:
    raw = rollout(model) if callable(rollout) else rollout
    frames = [np.asarray(q, dtype=np.float64) for q in raw]
    if not frames:
        raise ValueError("rollout must contain at least one configuration")
    for i, q in enumerate(frames):
        require_shape(q, (model.nq,), f"rollout[{i}]")
        require_finite(q, f"rollout[{i}]")
    return frames


def _render_animation_html(
    model: Any, urdf: str, frames: list[np.ndarray], fps: int
) -> str:
    """Replay *frames* into a private localhost Meshcat server; return its HTML."""
    try:
        import meshcat
        import meshcat.animation
    except ImportError as exc:  # pragma: no cover - exercised without meshcat
        raise ImportError(
            "Recording needs meshcat. Install with: "
            "pip install pinocchio-models[meshcat]"
        ) from exc
    import pinocchio as pin
    from pinocchio.visualize import MeshcatVisualizer

    visual_model = pin.buildGeomFromUrdfString(model, urdf, pin.GeometryType.VISUAL)
    viewer = meshcat.Visualizer()  # server binds 127.0.0.1; never opened
    try:
        viz = MeshcatVisualizer(model, visual_model, visual_model)
        viz.initViewer(viewer=viewer, open=False)
        viz.loadViewerModel()
        viz.display(frames[0])

        animation = meshcat.animation.Animation(default_framerate=int(fps))
        for index, q in enumerate(frames):
            with animation.at_frame(viewer, index) as frame:
                viz.viewer = frame  # record placements instead of sending them
                viz.display(q)
        viz.viewer = viewer
        viewer.set_animation(animation, play=True, repetitions=1)
        html: str = viewer.static_html()
    finally:
        _shutdown(viewer)
    return html


def _shutdown(viewer: Any) -> None:
    """Stop the private Meshcat server started for one recording."""
    window = viewer.window
    window.zmq_socket.close(linger=0)
    proc = window.server_proc
    if proc is not None and proc.poll() is None:
        proc.kill()
        proc.wait()


def _ensure_recording(recording: RolloutRecording) -> None:
    if recording.size_bytes <= 0:
        raise RuntimeError(f"recording {recording.path} is empty")
    stored = recorded_frame_count(recording.path)
    if stored != recording.frame_count:
        raise RuntimeError(
            f"recording {recording.path} stores {stored} frames, "
            f"expected {recording.frame_count}"
        )


__all__ = ["Rollout", "RolloutRecording", "record_rollout", "recorded_frame_count"]
