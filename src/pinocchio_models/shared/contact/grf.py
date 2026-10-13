"""Ground reaction force (GRF) and centre of pressure (CoP) aggregation (#432).

Engine-independent math that turns per-point contact forces into per-foot and
total ground reaction wrenches plus a centre of pressure. The Pinocchio
adapter (:mod:`pinocchio_models.contact_dynamics`) solves the contact forces;
everything here is plain NumPy so it is unit-tested without an engine.

Conventions (canonical frame: X forward, Y left, Z up, floor at ``z = 0``):

* Forces are the forces the ground applies **on** the body, in world axes (N).
* Moments are taken about the world origin (N m).
* The CoP is the point on the ground plane where the horizontal moment of the
  wrench vanishes. It is ``None`` whenever the normal (vertical) force is not
  positive -- in particular in the **no-contact** case, where every force and
  moment is exactly zero.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike

from robotics_contracts.preconditions import (
    require_finite,
    require_non_negative,
    require_shape,
)

#: Normal force (N) at or below which no centre of pressure is defined.
MIN_NORMAL_FORCE_N: float = 1e-9


@dataclass(frozen=True)
class ContactForceSample:
    """Force the ground applies at one contact point.

    Attributes:
        foot: Name of the foot (body frame) the point belongs to.
        position: World position of the point, shape ``(3,)`` (m).
        force: Ground force on the body at the point, shape ``(3,)`` (N).
    """

    foot: str
    position: np.ndarray
    force: np.ndarray


@dataclass(frozen=True)
class FootGRF:
    """Ground reaction wrench on one foot.

    Attributes:
        name: Foot (body frame) name, e.g. ``"foot_l"``.
        force: Total ground force on the foot, shape ``(3,)`` (N).
        moment: Moment of that force about the world origin, shape ``(3,)``.
        cop: Centre of pressure on the ground plane, shape ``(3,)``, or
            ``None`` when the foot carries no positive normal force.
        in_contact: Whether any contact point of the foot is active.
    """

    name: str
    force: np.ndarray
    moment: np.ndarray
    cop: np.ndarray | None
    in_contact: bool


@dataclass(frozen=True)
class GroundReactionForces:
    """Per-foot and total ground reaction forces with centre of pressure.

    Attributes:
        per_foot: Wrench of every requested foot, keyed by foot name. Feet
            without active contacts carry zero force and ``cop=None``.
        total_force: Sum of the per-foot forces, shape ``(3,)`` (N).
        total_moment: Sum of the per-foot moments about the origin, ``(3,)``.
        cop: Centre of pressure of the total wrench, or ``None`` when no
            positive normal force acts (e.g. no contact).
        support_polygon: Counter-clockwise convex hull ``(k, 2)`` of the
            active contact points' ground projections; ``(0, 2)`` if none.
    """

    per_foot: dict[str, FootGRF]
    total_force: np.ndarray
    total_moment: np.ndarray
    cop: np.ndarray | None
    support_polygon: np.ndarray

    @property
    def in_contact(self) -> bool:
        """Whether any foot is in contact with the ground."""
        return any(foot.in_contact for foot in self.per_foot.values())


def center_of_pressure(
    force: ArrayLike,
    moment: ArrayLike,
    ground_height: float = 0.0,
    min_normal_force: float = MIN_NORMAL_FORCE_N,
) -> np.ndarray | None:
    """Return the centre of pressure of a wrench on the plane ``z = ground_height``.

    The wrench ``(force, moment)`` has its moment about the world origin. The
    CoP ``p`` is the ground-plane point where the moment's horizontal
    components vanish: ``moment = p x force + (0, 0, m_free)``, so
    ``p_x = (h F_x - M_y) / F_z`` and ``p_y = (M_x + h F_y) / F_z``.

    Args:
        force: Ground force, shape ``(3,)``.
        moment: Moment about the world origin, shape ``(3,)``.
        ground_height: Height ``h`` of the ground plane.
        min_normal_force: ``F_z`` at or below which the CoP is undefined.

    Returns:
        CoP ``(p_x, p_y, h)``, or ``None`` when ``F_z <= min_normal_force``.

    Raises:
        ValueError: Wrong shape or non-finite input, negative threshold.
    """
    f = _vec3(force, "force")
    m = _vec3(moment, "moment")
    require_finite(np.array([ground_height]), "ground_height")
    require_non_negative(min_normal_force, "min_normal_force")
    if f[2] <= min_normal_force:
        return None
    h = float(ground_height)
    return np.array([(h * f[0] - m[1]) / f[2], (m[0] + h * f[1]) / f[2], h])


def convex_hull_2d(points: ArrayLike) -> np.ndarray:
    """Return the counter-clockwise convex hull of 2-D points (monotone chain).

    Collinear and duplicate points are dropped. Fewer than three distinct
    points return the distinct points themselves (a point or a segment).

    Args:
        points: Array of shape ``(n, 2)``; ``n`` may be zero.

    Returns:
        Hull vertices, shape ``(k, 2)``.
    """
    pts = np.asarray(points, dtype=np.float64).reshape(-1, 2)
    require_finite(pts, "points")
    unique = sorted({(float(x), float(y)) for x, y in pts})
    if len(unique) < 3:
        return np.array(unique, dtype=np.float64).reshape(-1, 2)

    def _half(seq: Iterable[tuple[float, float]]) -> list[tuple[float, float]]:
        chain: list[tuple[float, float]] = []
        for p in seq:
            while len(chain) >= 2 and _cross(chain[-2], chain[-1], p) <= 0.0:
                chain.pop()
            chain.append(p)
        return chain

    lower = _half(unique)
    upper = _half(reversed(unique))
    return np.array(lower[:-1] + upper[:-1], dtype=np.float64)


def point_in_convex_polygon(
    point: ArrayLike, polygon: ArrayLike, tol: float = 1e-9
) -> bool:
    """Return whether a 2-D point lies inside (or on) a counter-clockwise hull.

    Args:
        point: Shape ``(2,)`` (extra trailing coordinates are ignored).
        polygon: Counter-clockwise convex polygon ``(k, 2)`` with ``k >= 3``,
            as returned by :func:`convex_hull_2d`.
        tol: Distance (m) outside an edge still counted as inside.

    Returns:
        ``True`` when the point is inside the polygon within ``tol``.

    Raises:
        ValueError: Degenerate polygon (fewer than three vertices).
    """
    p = np.asarray(point, dtype=np.float64).ravel()[:2]
    poly = np.asarray(polygon, dtype=np.float64).reshape(-1, 2)
    if len(poly) < 3:
        raise ValueError(f"polygon needs at least 3 vertices, got {len(poly)}")
    require_non_negative(tol, "tol")
    for a, b in zip(poly, np.roll(poly, -1, axis=0), strict=True):
        edge = b - a
        # Signed distance of p to the left of edge a->b (inside is positive).
        if _cross(a, b, p) / float(np.hypot(*edge)) < -tol:
            return False
    return True


def aggregate_ground_reaction(
    samples: Sequence[ContactForceSample],
    feet: Sequence[str],
    ground_height: float = 0.0,
) -> GroundReactionForces:
    """Sum active contact-point forces into per-foot and total GRF with CoP.

    Every foot in *feet* appears in the result. A foot with no samples is
    explicitly out of contact: zero force and moment, ``cop=None``. With no
    samples at all the result is the no-contact case (all zero, ``cop=None``,
    empty support polygon).

    Args:
        samples: Active contact points and their ground forces.
        feet: Names of every foot to report.
        ground_height: Height of the ground plane for the CoP.

    Returns:
        The aggregated :class:`GroundReactionForces`.

    Raises:
        ValueError: A sample names a foot not in *feet*, or has a wrong
            shape or non-finite values; duplicate foot names.
    """
    if len(set(feet)) != len(feet):
        raise ValueError(f"duplicate foot names in {list(feet)}")
    forces = {name: np.zeros(3) for name in feet}
    moments = {name: np.zeros(3) for name in feet}
    active: dict[str, bool] = dict.fromkeys(feet, False)
    for sample in samples:
        if sample.foot not in forces:
            raise ValueError(f"sample foot {sample.foot!r} not in feet {list(feet)}")
        position = _vec3(sample.position, "position")
        force = _vec3(sample.force, "force")
        forces[sample.foot] += force
        moments[sample.foot] += np.cross(position, force)
        active[sample.foot] = True

    per_foot = {
        name: FootGRF(
            name=name,
            force=forces[name],
            moment=moments[name],
            cop=center_of_pressure(forces[name], moments[name], ground_height),
            in_contact=active[name],
        )
        for name in feet
    }
    total_force = np.sum([forces[name] for name in feet], axis=0).reshape(3)
    total_moment = np.sum([moments[name] for name in feet], axis=0).reshape(3)
    hull_points = np.array(
        [_vec3(s.position, "position")[:2] for s in samples], dtype=np.float64
    ).reshape(-1, 2)
    result = GroundReactionForces(
        per_foot=per_foot,
        total_force=total_force,
        total_moment=total_moment,
        cop=center_of_pressure(total_force, total_moment, ground_height),
        support_polygon=convex_hull_2d(hull_points),
    )
    _ensure_no_contact_is_zero(result)
    return result


def _ensure_no_contact_is_zero(result: GroundReactionForces) -> None:
    """Postcondition: without contact, force and moment are zero, CoP None."""
    if result.in_contact:
        return
    wrench = np.concatenate([result.total_force, result.total_moment])
    if np.any(wrench) or result.cop is not None:
        raise ValueError("no-contact result must have zero wrench and cop=None")


def _cross(o: ArrayLike, a: ArrayLike, b: ArrayLike) -> float:
    """2-D cross product of ``a - o`` and ``b - o`` (positive = left turn)."""
    o_, a_, b_ = (np.asarray(v, dtype=np.float64) for v in (o, a, b))
    return float((a_[0] - o_[0]) * (b_[1] - o_[1]) - (a_[1] - o_[1]) * (b_[0] - o_[0]))


def _vec3(value: ArrayLike, name: str) -> np.ndarray:
    """Return *value* as a finite float ``(3,)`` array or raise ``ValueError``."""
    arr = np.asarray(value, dtype=np.float64)
    require_shape(arr, (3,), name)
    require_finite(arr, name)
    return arr


__all__ = [
    "MIN_NORMAL_FORCE_N",
    "ContactForceSample",
    "FootGRF",
    "GroundReactionForces",
    "aggregate_ground_reaction",
    "center_of_pressure",
    "convex_hull_2d",
    "point_in_convex_polygon",
]
