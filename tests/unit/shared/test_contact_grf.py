"""Engine-independent GRF / CoP aggregation (issue #432)."""

from __future__ import annotations

import numpy as np
import pytest

from pinocchio_models.shared.contact import foot_contact_points, get_exercise_contacts
from pinocchio_models.shared.contact.grf import (
    ContactForceSample,
    aggregate_ground_reaction,
    center_of_pressure,
    convex_hull_2d,
    point_in_convex_polygon,
)

FEET = ("foot_l", "foot_r")


def _sample(foot: str, x: float, y: float, fz: float) -> ContactForceSample:
    return ContactForceSample(
        foot=foot, position=np.array([x, y, 0.0]), force=np.array([0.0, 0.0, fz])
    )


class TestCenterOfPressure:
    def test_single_point_force_cop_is_the_point(self) -> None:
        p, f = np.array([0.3, -0.2, 0.0]), np.array([1.0, 2.0, 50.0])
        cop = center_of_pressure(f, np.cross(p, f))
        assert cop is not None
        np.testing.assert_allclose(cop, p, atol=1e-12)

    def test_free_moment_does_not_shift_cop(self) -> None:
        p, f = np.array([0.1, 0.05, 0.0]), np.array([0.0, 0.0, 100.0])
        cop = center_of_pressure(f, np.cross(p, f) + np.array([0.0, 0.0, 7.0]))
        assert cop is not None
        np.testing.assert_allclose(cop, p, atol=1e-12)

    def test_raised_ground_plane(self) -> None:
        p, f = np.array([0.2, 0.1, 0.5]), np.array([3.0, -4.0, 60.0])
        cop = center_of_pressure(f, np.cross(p, f), ground_height=0.5)
        assert cop is not None
        np.testing.assert_allclose(cop, p, atol=1e-12)

    @pytest.mark.parametrize("fz", [0.0, -10.0, 1e-12])
    def test_no_positive_normal_force_has_no_cop(self, fz: float) -> None:
        assert center_of_pressure([0.0, 0.0, fz], [0.0, 0.0, 0.0]) is None

    def test_rejects_bad_shape_and_values(self) -> None:
        with pytest.raises(ValueError, match="force must have shape"):
            center_of_pressure([0.0, 1.0], [0.0, 0.0, 0.0])
        with pytest.raises(ValueError, match="non-finite"):
            center_of_pressure([0.0, 0.0, 1.0], [np.nan, 0.0, 0.0])
        with pytest.raises(ValueError, match="min_normal_force"):
            center_of_pressure([0.0, 0.0, 1.0], [0.0, 0.0, 0.0], min_normal_force=-1)


class TestConvexHull:
    def test_square_with_interior_and_collinear_points(self) -> None:
        pts = [(0, 0), (1, 0), (1, 1), (0, 1), (0.5, 0.5), (0.5, 0.0), (0, 0)]
        hull = convex_hull_2d(pts)
        assert {tuple(v) for v in hull} == {(0, 0), (1, 0), (1, 1), (0, 1)}
        # Counter-clockwise: positive shoelace area.
        x, y = hull[:, 0], hull[:, 1]
        assert 0.5 * np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y) == 1.0

    @pytest.mark.parametrize("n", [0, 1, 2])
    def test_degenerate_inputs(self, n: int) -> None:
        pts = np.array([(0.0, 0.0), (1.0, 0.0)])[:n]
        assert convex_hull_2d(pts).shape == (n, 2)


class TestPointInPolygon:
    square = convex_hull_2d([(0, 0), (1, 0), (1, 1), (0, 1)])

    @pytest.mark.parametrize(
        ("point", "inside"),
        [((0.5, 0.5), True), ((1.0, 0.5), True), ((1.01, 0.5), False)],
    )
    def test_membership(self, point: tuple[float, float], inside: bool) -> None:
        assert point_in_convex_polygon(point, self.square) is inside

    def test_tolerance_and_extra_coordinate(self) -> None:
        assert point_in_convex_polygon((1.005, 0.5, 9.0), self.square, tol=0.01)

    def test_degenerate_polygon_rejected(self) -> None:
        with pytest.raises(ValueError, match="at least 3 vertices"):
            point_in_convex_polygon((0, 0), [(0, 0), (1, 0)])


class TestAggregate:
    def test_two_feet_per_foot_total_and_cop(self) -> None:
        samples = [
            _sample("foot_l", 0.1, 0.1, 30.0),
            _sample("foot_l", -0.1, 0.1, 10.0),
            _sample("foot_r", 0.0, -0.1, 40.0),
        ]
        grf = aggregate_ground_reaction(samples, FEET)

        assert grf.in_contact
        np.testing.assert_allclose(grf.per_foot["foot_l"].force, [0, 0, 40.0])
        np.testing.assert_allclose(grf.per_foot["foot_r"].force, [0, 0, 40.0])
        np.testing.assert_allclose(grf.total_force, [0, 0, 80.0])
        left_cop = grf.per_foot["foot_l"].cop
        assert left_cop is not None
        np.testing.assert_allclose(left_cop, [0.05, 0.1, 0.0], atol=1e-12)
        assert grf.cop is not None
        # Force-weighted mean of the point positions.
        np.testing.assert_allclose(grf.cop, [0.025, 0.0, 0.0], atol=1e-12)
        assert point_in_convex_polygon(grf.cop, grf.support_polygon)
        assert grf.support_polygon.shape == (3, 2)

    def test_no_contact_is_explicit_zero_and_none(self) -> None:
        grf = aggregate_ground_reaction([], FEET)

        assert not grf.in_contact
        assert grf.cop is None
        np.testing.assert_array_equal(grf.total_force, np.zeros(3))
        np.testing.assert_array_equal(grf.total_moment, np.zeros(3))
        assert grf.support_polygon.shape == (0, 2)
        assert set(grf.per_foot) == set(FEET)
        for foot in grf.per_foot.values():
            assert not foot.in_contact
            assert foot.cop is None
            np.testing.assert_array_equal(foot.force, np.zeros(3))

    def test_one_foot_airborne(self) -> None:
        grf = aggregate_ground_reaction([_sample("foot_r", 0.0, -0.1, 50.0)], FEET)

        assert grf.per_foot["foot_r"].in_contact
        assert not grf.per_foot["foot_l"].in_contact
        assert grf.per_foot["foot_l"].cop is None

    def test_rejects_unknown_foot_and_duplicates(self) -> None:
        with pytest.raises(ValueError, match="not in feet"):
            aggregate_ground_reaction([_sample("hand_l", 0, 0, 1.0)], FEET)
        with pytest.raises(ValueError, match="duplicate foot names"):
            aggregate_ground_reaction([], ("foot_l", "foot_l"))

    def test_rejects_non_finite_sample(self) -> None:
        with pytest.raises(ValueError, match="non-finite"):
            aggregate_ground_reaction([_sample("foot_l", np.nan, 0, 1.0)], FEET)


def test_foot_contact_points_match_exercise_spec() -> None:
    points = foot_contact_points()
    assert points == get_exercise_contacts("gait").foot_contacts
    assert [p.frame_name for p in points] == ["foot_l"] * 4 + ["foot_r"] * 4
