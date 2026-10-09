"""Real-Pinocchio inverse dynamics (RNEA) checks for every manifest exercise.

Pinocchio is a ``dev`` dependency, so this runs in default CI (issue #431).
"""

from __future__ import annotations

import numpy as np
import pinocchio as pin
import pytest

from pinocchio_models import inverse_dynamics
from pinocchio_models.model_pack import list_exercises
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

EXERCISES = list_exercises()


def _model(exercise: str) -> pin.Model:
    return load_model(build_urdf(exercise))


@pytest.mark.parametrize("exercise", EXERCISES)
def test_static_pose_matches_rnea_and_root_force_is_mg(exercise: str) -> None:
    model = _model(exercise)
    q = pin.neutral(model)
    zeros = np.zeros(model.nv)

    tau = inverse_dynamics(exercise, q, zeros, zeros)

    np.testing.assert_allclose(
        tau, pin.rnea(model, model.createData(), q, zeros, zeros), rtol=1e-12
    )
    total_mass = sum(inertia.mass for inertia in model.inertias)
    weight = total_mass * -model.gravity.linear[2]
    assert tau[2] == pytest.approx(weight, rel=1e-6)


def test_moving_pose_matches_rnea() -> None:
    model = _model("squat")
    rng = np.random.default_rng(0)
    q = pin.integrate(model, pin.neutral(model), 0.05 * rng.standard_normal(model.nv))
    v = 0.1 * rng.standard_normal(model.nv)
    a = 0.5 * rng.standard_normal(model.nv)

    tau = inverse_dynamics("squat", q, v, a)

    np.testing.assert_allclose(
        tau, pin.rnea(model, model.createData(), q, v, a), rtol=1e-12
    )
    assert not np.allclose(tau, inverse_dynamics("squat", q, 0 * v, 0 * a))


def test_accepts_prebuilt_model() -> None:
    model = _model("squat")
    zeros = np.zeros(model.nv)
    np.testing.assert_allclose(
        inverse_dynamics(model, pin.neutral(model), zeros, zeros),
        inverse_dynamics("squat", pin.neutral(model), zeros, zeros),
    )


class TestPreconditions:
    def setup_method(self) -> None:
        self.model = _model("squat")
        self.q = pin.neutral(self.model)
        self.zeros = np.zeros(self.model.nv)

    def test_unknown_exercise(self) -> None:
        with pytest.raises(ValueError, match="unknown exercise"):
            inverse_dynamics("nope", self.q, self.zeros, self.zeros)

    def test_wrong_type(self) -> None:
        with pytest.raises(TypeError, match="exercise must be"):
            inverse_dynamics(42, self.q, self.zeros, self.zeros)  # type: ignore[arg-type]

    @pytest.mark.parametrize("bad", ["q", "v", "a"])
    def test_wrong_shape(self, bad: str) -> None:
        args = {"q": self.q, "v": self.zeros, "a": self.zeros}
        args[bad] = np.zeros(3)
        with pytest.raises(ValueError, match=f"{bad} must have shape"):
            inverse_dynamics("squat", args["q"], args["v"], args["a"])

    @pytest.mark.parametrize("bad", ["q", "v", "a"])
    @pytest.mark.parametrize("value", [np.nan, np.inf])
    def test_non_finite(self, bad: str, value: float) -> None:
        args = {"q": self.q.copy(), "v": self.zeros.copy(), "a": self.zeros.copy()}
        args[bad][0] = value
        with pytest.raises(ValueError, match="non-finite"):
            inverse_dynamics("squat", args["q"], args["v"], args["a"])
