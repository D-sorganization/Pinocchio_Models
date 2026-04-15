"""Anthropometric data and bilateral assembly helpers for the full-body model.

Contains:
  - ``BodyModelSpec``        -- anthropometric specification dataclass
  - ``_SEGMENT_TABLE``       -- Winter (2009) mass/length/radius fractions
  - ``_BILATERAL_SEGMENTS``  -- frozenset of segments that appear bilaterally
  - ``_seg()``               -- compute (mass, length, radius) for a segment
  - ``_add_bilateral_limb_simple()``  -- add left/right 1-DOF joints
  - ``_add_bilateral_ndof()``         -- add left/right N-DOF compound joints

Anthropometric defaults are for a 50th-percentile male (height=1.75 m,
mass=80 kg) following Winter (2009) segment proportions.

Law of Demeter: callers use ``create_full_body()`` from ``body_model`` and
never touch segment internals directly.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from pinocchio_models.shared.contracts.preconditions import (
    require_positive,
)
from pinocchio_models.shared.utils.geometry import (
    cylinder_inertia,
)
from pinocchio_models.shared.utils.urdf_helpers import (
    add_link,
    add_revolute_joint,
    add_virtual_link,
    make_cylinder_geometry,
)


@dataclass(frozen=True)
class BodyModelSpec:
    """Anthropometric specification for the full-body model.

    All lengths in meters, mass in kg.
    """

    total_mass: float = 80.0
    height: float = 1.75

    def __post_init__(self) -> None:
        require_positive(self.total_mass, "total_mass")
        require_positive(self.height, "height")


# Winter (2009) segment mass fractions and length fractions of total height.
_SEGMENT_TABLE: dict[str, dict[str, float]] = {
    "pelvis": {"mass_frac": 0.142, "length_frac": 0.100, "radius_frac": 0.085},
    "torso": {"mass_frac": 0.355, "length_frac": 0.288, "radius_frac": 0.080},
    "head": {"mass_frac": 0.081, "length_frac": 0.130, "radius_frac": 0.060},
    "upper_arm": {"mass_frac": 0.028, "length_frac": 0.186, "radius_frac": 0.023},
    "forearm": {"mass_frac": 0.016, "length_frac": 0.146, "radius_frac": 0.018},
    "hand": {"mass_frac": 0.006, "length_frac": 0.050, "radius_frac": 0.020},
    "thigh": {"mass_frac": 0.100, "length_frac": 0.245, "radius_frac": 0.037},
    "shank": {"mass_frac": 0.047, "length_frac": 0.246, "radius_frac": 0.025},
    "foot": {"mass_frac": 0.014, "length_frac": 0.040, "radius_frac": 0.025},
}


# Segments that are duplicated bilaterally (_l and _r suffixes).
# Central segments (pelvis, torso, head) are NOT bilateral and must
# NOT be resolved with a side suffix.
_BILATERAL_SEGMENTS: frozenset[str] = frozenset(
    {"upper_arm", "forearm", "hand", "thigh", "shank", "foot"}
)


def _seg(spec: BodyModelSpec, name: str) -> tuple[float, float, float]:
    """Return (mass, length, radius) for a named segment."""
    s = _SEGMENT_TABLE[name]
    mass = spec.total_mass * s["mass_frac"]
    length = spec.height * s["length_frac"]
    radius = spec.height * s["radius_frac"]
    return mass, length, radius


def _resolve_bilateral_parent(parent_name: str, side: str) -> str:
    """Return the actual parent-link name for *side*.

    Bilateral segments (e.g. ``thigh``) must be suffixed with ``_l`` or
    ``_r`` to match the link created on that side; central segments
    (``pelvis``, ``torso``) already carry their own name and are returned
    unchanged.
    """
    if parent_name in _BILATERAL_SEGMENTS:
        return f"{parent_name}_{side}"
    return parent_name


def _add_limb_side_simple(
    robot: ET.Element,
    *,
    side: str,
    sign: float,
    seg_name: str,
    parent_name: str,
    mass: float,
    length: float,
    radius: float,
    inertia: tuple[float, float, float],
    parent_offset_z: float,
    parent_lateral_y: float,
    coord_prefix: str,
    range_min: float,
    range_max: float,
) -> None:
    """Add a single-DOF limb segment (link + revolute joint) for one side."""
    body_name = f"{seg_name}_{side}"
    add_link(
        robot,
        name=body_name,
        mass=mass,
        origin_xyz=(0, 0, -length / 2.0),
        ixx=inertia[0],
        iyy=inertia[1],
        izz=inertia[2],
        visual_geometry=make_cylinder_geometry(radius, length),
    )
    add_revolute_joint(
        robot,
        name=f"{coord_prefix}_{side}",
        parent=_resolve_bilateral_parent(parent_name, side),
        child=body_name,
        origin_xyz=(0, sign * parent_lateral_y, parent_offset_z),
        axis=(0, 1, 0),
        lower=range_min,
        upper=range_max,
    )


def _add_bilateral_limb_simple(
    robot: ET.Element,
    spec: BodyModelSpec,
    *,
    seg_name: str,
    parent_name: str,
    parent_offset_z: float,
    parent_lateral_y: float,
    coord_prefix: str,
    range_min: float,
    range_max: float,
) -> None:
    """Add left and right limb segments with a single revolute joint each.

    Used for simple 1-DOF joints (elbow, knee).
    Z-up convention: vertical offset is in Z, lateral is in Y.
    Joint axis is Y (sagittal-plane flexion/extension).
    """
    mass, length, radius = _seg(spec, seg_name)
    inertia = cylinder_inertia(mass, radius, length)

    for side, sign in (("l", -1.0), ("r", 1.0)):
        _add_limb_side_simple(
            robot,
            side=side,
            sign=sign,
            seg_name=seg_name,
            parent_name=parent_name,
            mass=mass,
            length=length,
            radius=radius,
            inertia=inertia,
            parent_offset_z=parent_offset_z,
            parent_lateral_y=parent_lateral_y,
            coord_prefix=coord_prefix,
            range_min=range_min,
            range_max=range_max,
        )


def _add_bilateral_ndof(
    robot: ET.Element,
    spec: BodyModelSpec,
    *,
    seg_name: str,
    parent_name: str,
    parent_offset_z: float,
    parent_lateral_y: float,
    coord_prefix: str,
    joints: list[tuple[str, tuple[float, float, float], float, float]],
) -> None:
    """Add bilateral N-DOF compound joint with N-1 virtual links per side.

    Creates the chain:
        parent -> [joint 1] -> virtual_1 -> [joint 2] -> ... -> real body link
    """
    mass, length, radius = _seg(spec, seg_name)
    inertia = cylinder_inertia(mass, radius, length)

    for side, sign in [("l", -1.0), ("r", 1.0)]:
        body_name = f"{seg_name}_{side}"
        parent_full = (
            f"{parent_name}_{side}" if parent_name in _SEGMENT_TABLE else parent_name
        )

        current_parent = parent_full

        for i, (jname, jaxis, jmin, jmax) in enumerate(joints):
            is_last = i == len(joints) - 1

            if not is_last:
                virt_name = f"{coord_prefix}_{side}_virtual_{i + 1}"
                add_virtual_link(robot, name=virt_name)
                child_name = virt_name
            else:
                # The real body link is created before the final joint
                # to maintain the order in the XML structure identical to before.
                add_link(
                    robot,
                    name=body_name,
                    mass=mass,
                    origin_xyz=(0, 0, -length / 2.0),
                    ixx=inertia[0],
                    iyy=inertia[1],
                    izz=inertia[2],
                    visual_geometry=make_cylinder_geometry(radius, length),
                )
                child_name = body_name

            origin_xyz = (
                (0, sign * parent_lateral_y, parent_offset_z) if i == 0 else (0, 0, 0)
            )

            add_revolute_joint(
                robot,
                name=f"{coord_prefix}_{side}_{jname}",
                parent=current_parent,
                child=child_name,
                origin_xyz=origin_xyz,
                axis=jaxis,
                lower=jmin,
                upper=jmax,
            )
            current_parent = child_name
