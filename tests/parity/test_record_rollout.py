"""Headless Meshcat recording of an exercise rollout (issue #438).

Runs a short kinematic replay through :func:`record_rollout` with a real
Pinocchio ``MeshcatVisualizer`` and a private ``127.0.0.1`` Meshcat server,
then decodes the written HTML to check the frame count. Skips when the
optional ``meshcat`` extra is not installed.
"""

from __future__ import annotations

import webbrowser
from pathlib import Path

import numpy as np
import pinocchio as pin
import pytest

from pinocchio_models import record_rollout
from pinocchio_models.recording import recorded_frame_count
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

pytest.importorskip("meshcat")

FRAMES = 12


def _squat_replay(model: pin.Model, n: int = FRAMES) -> list[np.ndarray]:
    """Interpolate from neutral to the mid-range of every joint's limits."""
    start = pin.neutral(model)
    end = start.copy()
    mid = 0.5 * (model.lowerPositionLimit[7:] + model.upperPositionLimit[7:])
    end[7:] = np.where(np.isfinite(mid), mid, 0.0)
    return [pin.interpolate(model, start, end, t) for t in np.linspace(0, 1, n)]


@pytest.fixture(autouse=True)
def _no_browser(monkeypatch: pytest.MonkeyPatch) -> None:
    def _refuse(*_args: object, **_kwargs: object) -> bool:
        raise AssertionError("record_rollout must never open a browser")

    monkeypatch.setattr(webbrowser, "open", _refuse)


def test_records_sequence_with_expected_frame_count(tmp_path: Path) -> None:
    model = load_model(build_urdf("squat"))
    out = tmp_path / "squat.html"

    recording = record_rollout("squat", _squat_replay(model), out, fps=24)

    assert recording.path == out
    assert out.is_file()
    assert recording.size_bytes == out.stat().st_size > 0
    assert recording.frame_count == FRAMES
    assert recorded_frame_count(out) == FRAMES
    assert recording.duration_s == pytest.approx(FRAMES / 24)
    html = out.read_text(encoding="utf-8")
    assert "MeshCat.Viewer" in html


def test_records_callable_rollout(tmp_path: Path) -> None:
    out = tmp_path / "gait.html"

    recording = record_rollout("gait", lambda model: _squat_replay(model, 5), out)

    assert recording.frame_count == 5
    assert recorded_frame_count(out) == 5


def test_meshcat_server_is_localhost_and_shut_down(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    import meshcat.visualizer

    started: list[tuple[object, str]] = []
    real_start = meshcat.visualizer.start_zmq_server_as_subprocess

    def _spy(*args: object, **kwargs: object) -> tuple[object, str, str]:
        proc, zmq_url, web_url = real_start(*args, **kwargs)
        started.append((proc, web_url))
        return proc, zmq_url, web_url

    monkeypatch.setattr(meshcat.visualizer, "start_zmq_server_as_subprocess", _spy)
    model = load_model(build_urdf("squat"))

    for i in range(2):
        record_rollout("squat", _squat_replay(model, 3), tmp_path / f"r{i}.html")

    assert len(started) == 2
    for proc, web_url in started:
        assert "127.0.0.1" in web_url
        assert proc.poll() is not None  # type: ignore[attr-defined]
