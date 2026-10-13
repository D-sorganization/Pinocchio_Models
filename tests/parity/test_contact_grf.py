"""Real-Pinocchio constrained contact dynamics: GRF and CoP (issue #432).

Pinocchio is a ``dev`` dependency, so this runs in default CI (as
``test_inverse_dynamics.py`` does).
"""

from __future__ import annotations

import numpy as np
import pinocchio as pin
import pytest

from pinocchio_models import ground_configuration, ground_reaction_forces
from pinocchio_models.model_pack import list_exercises
from pinocchio_models.shared.contact.grf import point_in_convex_polygon
from pinocchio_models.shared.parity._canonical import conformance, spec
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

FEET = ("foot_l", "foot_r")
STANDING = ("gait", "squat")
FREE_ROOT = [
    ex
    for ex in list_exercises()
    if spec.root_joint(conformance.load_standard(), ex) == "free"
]


def _model(exercise: str) -> pin.Model:
    return load_model(build_urdf(exercise))


def _standing_q(model: pin.Model) -> np.ndarray:
    return ground_configuration(model, pin.neutral(model))


def _weight(model: pin.Model) -> float:
    return sum(i.mass for i in model.inertias) * -model.gravity.linear[2]


@pytest.mark.parametrize("exercise", STANDING)
def test_standing_vertical_grf_is_weight_and_cop_in_support(exercise: str) -> None:
    model = _model(exercise)

    grf = ground_reaction_forces(exercise, _standing_q(model))

    assert grf.total_force[2] == pytest.approx(_weight(model), rel=0.02)
    assert np.abs(grf.total_force[:2]).max() < 1e-3 * _weight(model)
    assert grf.cop is not None
    assert grf.cop[2] == pytest.approx(0.0, abs=1e-9)
    assert point_in_convex_polygon(grf.cop, grf.support_polygon)
    assert set(grf.per_foot) == set(FEET)
    for foot in grf.per_foot.values():
        assert foot.in_contact
        assert foot.force[2] > 0.0
        assert foot.cop is not None


@pytest.mark.parametrize("exercise", STANDING)
def test_per_foot_wrenches_sum_to_total(exercise: str) -> None:
    grf = ground_reaction_forces(exercise, _standing_q(_model(exercise)))

    np.testing.assert_allclose(
        sum(f.force for f in grf.per_foot.values()), grf.total_force, atol=1e-9
    )
    np.testing.assert_allclose(
        sum(f.moment for f in grf.per_foot.values()), grf.total_moment, atol=1e-9
    )


@pytest.mark.parametrize("exercise", FREE_ROOT)
def test_grounded_neutral_pose_carries_full_weight(exercise: str) -> None:
    model = _model(exercise)

    grf = ground_reaction_forces(model, _standing_q(model))

    assert grf.total_force[2] == pytest.approx(_weight(model), rel=0.02)


def test_cop_matches_com_ground_projection_for_symmetric_stance() -> None:
    model = _model("gait")
    q = _standing_q(model)
    com = pin.centerOfMass(model, model.createData(), q)

    grf = ground_reaction_forces("gait", q)

    assert grf.cop is not None
    np.testing.assert_allclose(grf.cop[:2], com[:2], atol=1e-3)


def test_no_contact_is_zero_force_and_no_cop() -> None:
    model = _model("gait")
    q = _standing_q(model)
    q[2] += 0.10  # lift the whole body 10 cm off the floor

    grf = ground_reaction_forces("gait", q)

    assert not grf.in_contact
    np.testing.assert_array_equal(grf.total_force, np.zeros(3))
    np.testing.assert_array_equal(grf.total_moment, np.zeros(3))
    assert grf.cop is None
    assert grf.support_polygon.shape == (0, 2)
    for foot in grf.per_foot.values():
        assert not foot.in_contact
        np.testing.assert_array_equal(foot.force, np.zeros(3))
        assert foot.cop is None


def test_lifted_foot_is_out_of_contact_with_zero_force() -> None:
    model = _model("gait")
    q = pin.neutral(model)
    roll = 0.1  # positive roll about +X lowers the right (-Y) foot
    q[3:7] = [np.sin(roll / 2.0), 0.0, 0.0, np.cos(roll / 2.0)]
    q = ground_configuration(model, q)

    grf = ground_reaction_forces("gait", q)

    right, left = grf.per_foot["foot_r"], grf.per_foot["foot_l"]
    assert right.in_contact
    assert not left.in_contact
    np.testing.assert_array_equal(left.force, np.zeros(3))
    assert left.cop is None
    np.testing.assert_allclose(right.force, grf.total_force)


class TestPreconditions:
    def setup_method(self) -> None:
        self.model = _model("gait")
        self.q = _standing_q(self.model)

    def test_welded_root_rejected(self) -> None:
        bench = _model("bench_press")
        with pytest.raises(ValueError, match="free-flyer"):
            ground_reaction_forces(bench, pin.neutral(bench))

    def test_wrong_shape(self) -> None:
        with pytest.raises(ValueError, match="q must have shape"):
            ground_reaction_forces("gait", np.zeros(3))

    @pytest.mark.parametrize("value", [np.nan, np.inf])
    def test_non_finite(self, value: float) -> None:
        q = self.q.copy()
        q[0] = value
        with pytest.raises(ValueError, match="non-finite"):
            ground_reaction_forces("gait", q)

    def test_negative_tolerance(self) -> None:
        with pytest.raises(ValueError, match="contact_tolerance_m"):
            ground_reaction_forces("gait", self.q, contact_tolerance_m=-1.0)

    def test_unknown_exercise(self) -> None:
        with pytest.raises(ValueError, match="unknown exercise"):
            ground_reaction_forces("nope", self.q)
