"""Real-Pinocchio forward kinematics checks for every manifest exercise.

Pinocchio is a ``dev`` dependency, so this runs in default CI (issue #428).
"""

from __future__ import annotations

import numpy as np
import pinocchio as pin
import pytest

from pinocchio_models import forward_kinematics
from pinocchio_models.model_pack import list_exercises
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

EXERCISES = list_exercises()


def _model(exercise: str) -> pin.Model:
    return load_model(build_urdf(exercise))


@pytest.mark.parametrize("exercise", EXERCISES)
def test_neutral_pose_matches_pinocchio_fk(exercise: str) -> None:
    model = _model(exercise)
    data = model.createData()
    q = pin.neutral(model)
    pin.forwardKinematics(model, data, q)
    pin.updateFramePlacements(model, data)

    poses = forward_kinematics(exercise, q)

    assert len(poses) == model.nframes
    for frame_id, frame in enumerate(model.frames):
        expected = data.oMf[frame_id]
        actual = poses[frame.name]
        np.testing.assert_allclose(actual.translation, expected.translation, atol=1e-9)
        np.testing.assert_allclose(actual.rotation, expected.rotation, atol=1e-9)
        assert actual.isApprox(expected, prec=1e-9)


def test_moving_pose_matches_pinocchio_fk() -> None:
    model = _model("squat")
    data = model.createData()
    rng = np.random.default_rng(0)
    q = pin.integrate(model, pin.neutral(model), 0.05 * rng.standard_normal(model.nv))
    pin.forwardKinematics(model, data, q)
    pin.updateFramePlacements(model, data)

    poses = forward_kinematics("squat", q)

    assert len(poses) == model.nframes
    for frame_id, frame in enumerate(model.frames):
        expected = data.oMf[frame_id]
        actual = poses[frame.name]
        np.testing.assert_allclose(actual.translation, expected.translation, atol=1e-9)
        np.testing.assert_allclose(actual.rotation, expected.rotation, atol=1e-9)
        assert actual.isApprox(expected, prec=1e-9)


def test_accepts_prebuilt_model() -> None:
    model = _model("squat")
    q = pin.neutral(model)
    poses_by_model = forward_kinematics(model, q)
    poses_by_name = forward_kinematics("squat", q)
    assert set(poses_by_model.keys()) == set(poses_by_name.keys())
    for name in poses_by_model:
        assert poses_by_model[name].isApprox(poses_by_name[name], prec=1e-12)


class TestPreconditions:
    def setup_method(self) -> None:
        self.model = _model("squat")
        self.q = pin.neutral(self.model)

    def test_unknown_exercise(self) -> None:
        with pytest.raises(ValueError, match="unknown exercise"):
            forward_kinematics("nope", self.q)

    def test_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="exercise must be"):
            forward_kinematics(42, self.q)  # type: ignore[arg-type]

    def test_wrong_shape(self) -> None:
        with pytest.raises(ValueError, match="q must have shape"):
            forward_kinematics("squat", np.zeros(3))

    @pytest.mark.parametrize("value", [np.nan, np.inf])
    def test_non_finite(self, value: float) -> None:
        q = self.q.copy()
        q[0] = value
        with pytest.raises(ValueError, match="non-finite"):
            forward_kinematics("squat", q)
