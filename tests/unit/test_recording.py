"""Contract tests for :mod:`pinocchio_models.recording` (issue #438).

Every precondition is checked before a Meshcat server is started, so these
run without the optional ``meshcat`` extra.
"""

from __future__ import annotations

import base64
from pathlib import Path

import numpy as np
import pinocchio as pin
import pytest

from pinocchio_models.recording import (
    RolloutRecording,
    record_rollout,
    recorded_frame_count,
)
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

pytestmark = pytest.mark.unit


def _neutral() -> np.ndarray:
    return np.asarray(pin.neutral(load_model(build_urdf("squat"))))


@pytest.mark.parametrize("fps", [0, -1, float("nan"), float("inf"), 12.5])
def test_rejects_bad_fps(tmp_path: Path, fps: float) -> None:
    with pytest.raises(ValueError, match="fps"):
        record_rollout("squat", [_neutral()], tmp_path / "a.html", fps=fps)


def test_rejects_non_html_output(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match=r"\.html"):
        record_rollout("squat", [_neutral()], tmp_path / "a.mp4")


def test_rejects_missing_output_directory(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="directory"):
        record_rollout("squat", [_neutral()], tmp_path / "missing" / "a.html")


def test_rejects_unknown_exercise(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="unknown exercise"):
        record_rollout("curl", [np.zeros(3)], tmp_path / "a.html")


def test_rejects_empty_rollout(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="at least one"):
        record_rollout("squat", [], tmp_path / "a.html")
    with pytest.raises(ValueError, match="at least one"):
        record_rollout("squat", lambda _model: iter(()), tmp_path / "a.html")


def test_rejects_wrong_shape_and_non_finite(tmp_path: Path) -> None:
    q = _neutral()
    with pytest.raises(ValueError, match=r"rollout\[1\]"):
        record_rollout("squat", [q, q[:-1]], tmp_path / "a.html")
    bad = q.copy()
    bad[0] = np.nan
    with pytest.raises(ValueError, match=r"rollout\[0\]"):
        record_rollout("squat", [bad], tmp_path / "a.html")


def test_duration_is_frames_over_fps(tmp_path: Path) -> None:
    rec = RolloutRecording(tmp_path / "a.html", frame_count=60, fps=30, size_bytes=1)
    assert rec.duration_s == pytest.approx(2.0)


def _html_with_animation(key_counts: list[int]) -> str:
    umsgpack = pytest.importorskip("umsgpack")
    tracks = [
        {"name": ".position", "keys": [{"time": i} for i in range(n)]}
        for n in key_counts
    ]
    command = {
        "type": "set_animation",
        "animations": [{"path": "/x", "clip": {"fps": 30, "tracks": tracks}}],
    }
    blob = base64.b64encode(umsgpack.packb(command)).decode()
    noise = base64.b64encode(umsgpack.packb({"type": "set_transform"})).decode()
    return (
        f'fetch("data:application/octet-binary;base64,{noise}")\n'
        f'fetch("data:application/octet-binary;base64,{blob}")\n'
    )


def test_recorded_frame_count_reads_animation(tmp_path: Path) -> None:
    path = tmp_path / "a.html"
    path.write_text(_html_with_animation([7, 7]), encoding="utf-8")
    assert recorded_frame_count(path) == 7


@pytest.mark.parametrize("counts", [[], [3, 4]])
def test_recorded_frame_count_rejects_missing_or_inconsistent(
    tmp_path: Path, counts: list[int]
) -> None:
    path = tmp_path / "a.html"
    path.write_text(_html_with_animation(counts), encoding="utf-8")
    with pytest.raises(ValueError, match="consistent animation"):
        recorded_frame_count(path)
