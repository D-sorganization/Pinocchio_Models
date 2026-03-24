"""Simplified full-body model for barbell exercises (URDF format).

Segments (bilateral where noted):
  pelvis, torso, head,
  upper_arm_{l,r}, forearm_{l,r}, hand_{l,r},
  thigh_{l,r}, shank_{l,r}, foot_{l,r}

Joints (URDF revolute joints, Z-up convention):
  pelvis is the root link (Pinocchio adds FreeFlyer programmatically),
  lumbar (revolute -- flexion/extension about Y-axis),
  neck (revolute),
  shoulder_{l,r} (revolute -- flexion only for v0.1),
  elbow_{l,r} (revolute),
  wrist_{l,r} (revolute),
  hip_{l,r} (revolute -- flexion/extension),
  knee_{l,r} (revolute),
  ankle_{l,r} (revolute)

Anthropometric defaults are for a 50th-percentile male (height=1.75 m,
mass=80 kg) following Winter (2009) segment proportions.

Convention: Z-up (vertical), X-forward. Pinocchio adds the floating
base programmatically via pin.JointModelFreeFlyer().

Law of Demeter: exercise modules call create_full_body() and receive
link elements -- they never manipulate segment internals.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from dataclasses import dataclass

from pinocchio_models.shared.constants import (
    ANKLE_FLEXION_MAX,
    ANKLE_FLEXION_MIN,
    ELBOW_FLEXION_MAX,
    ELBOW_FLEXION_MIN,
    HIP_FLEXION_MAX,
    HIP_FLEXION_MIN,
    HIP_LATERAL_FRAC_OF_HEIGHT,
    KNEE_FLEXION_MAX,
    KNEE_FLEXION_MIN,
    LUMBAR_FLEXION_MAX,
    LUMBAR_FLEXION_MIN,
    NECK_FLEXION_MAX,
    NECK_FLEXION_MIN,
    SHOULDER_FLEXION_MAX,
    SHOULDER_FLEXION_MIN,
    SHOULDER_HEIGHT_FRAC,
    SHOULDER_LATERAL_FRAC_OF_HEIGHT,
    WRIST_FLEXION_MAX,
    WRIST_FLEXION_MIN,
)
from pinocchio_models.shared.contracts.preconditions import (
    require_positive,
)
from pinocchio_models.shared.utils.geometry import (
    cylinder_inertia,
    rectangular_prism_inertia,
)
from pinocchio_models.shared.utils.urdf_helpers import (
    add_link,
    add_revolute_joint,
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


def _seg(spec: BodyModelSpec, name: str) -> tuple[float, float, float]:
    """Return (mass, length, radius) for a named segment."""
    s = _SEGMENT_TABLE[name]
    mass = spec.total_mass * s["mass_frac"]
    length = spec.height * s["length_frac"]
    radius = spec.height * s["radius_frac"]
    return mass, length, radius


def _add_bilateral_limb(
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
    """Add left and right limb segments with revolute joints.

    Z-up convention: vertical offset is in Z, lateral is in Y.
    Joint axis is Y (sagittal-plane flexion/extension).
    """
    mass, length, radius = _seg(spec, seg_name)
    inertia = cylinder_inertia(mass, radius, length)

    for side, sign in [("l", -1.0), ("r", 1.0)]:
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

        parent_full = (
            f"{parent_name}_{side}" if parent_name in _SEGMENT_TABLE else parent_name
        )
        add_revolute_joint(
            robot,
            name=f"{coord_prefix}_{side}",
            parent=parent_full,
            child=body_name,
            origin_xyz=(0, sign * parent_lateral_y, parent_offset_z),
            axis=(0, 1, 0),
            lower=range_min,
            upper=range_max,
        )


def create_full_body(
    robot: ET.Element,
    spec: BodyModelSpec | None = None,
) -> dict[str, ET.Element]:
    """Build the full-body model and append links/joints to the <robot>.

    The pelvis is the root link. Pinocchio adds the floating base
    programmatically via pin.JointModelFreeFlyer() when loading URDF.

    Returns dict of link name -> ET.Element for all created links.
    """
    if spec is None:
        spec = BodyModelSpec()

    links: dict[str, ET.Element] = {}

    # --- Pelvis (root link -- Pinocchio adds FreeFlyer) ---
    p_mass, p_len, p_rad = _seg(spec, "pelvis")
    p_inertia = rectangular_prism_inertia(p_mass, p_rad * 2, p_len, p_rad * 2)
    links["pelvis"] = add_link(
        robot,
        name="pelvis",
        mass=p_mass,
        origin_xyz=(0, 0, 0),
        ixx=p_inertia[0],
        iyy=p_inertia[1],
        izz=p_inertia[2],
    )

    # --- Torso ---
    t_mass, t_len, t_rad = _seg(spec, "torso")
    t_inertia = rectangular_prism_inertia(t_mass, t_rad * 2, t_len, t_rad * 2)
    links["torso"] = add_link(
        robot,
        name="torso",
        mass=t_mass,
        origin_xyz=(0, 0, t_len / 2.0),
        ixx=t_inertia[0],
        iyy=t_inertia[1],
        izz=t_inertia[2],
    )
    add_revolute_joint(
        robot,
        name="lumbar",
        parent="pelvis",
        child="torso",
        origin_xyz=(0, 0, p_len / 2.0),
        axis=(0, 1, 0),
        lower=LUMBAR_FLEXION_MIN,
        upper=LUMBAR_FLEXION_MAX,
    )

    # --- Head ---
    h_mass, h_len, h_rad = _seg(spec, "head")
    h_inertia = cylinder_inertia(h_mass, h_rad, h_len)
    links["head"] = add_link(
        robot,
        name="head",
        mass=h_mass,
        origin_xyz=(0, 0, h_len / 2.0),
        ixx=h_inertia[0],
        iyy=h_inertia[1],
        izz=h_inertia[2],
    )
    add_revolute_joint(
        robot,
        name="neck",
        parent="torso",
        child="head",
        origin_xyz=(0, 0, t_len),
        axis=(0, 1, 0),
        lower=NECK_FLEXION_MIN,
        upper=NECK_FLEXION_MAX,
    )

    # --- Arms ---
    shoulder_z = t_len * SHOULDER_HEIGHT_FRAC
    shoulder_y = spec.height * SHOULDER_LATERAL_FRAC_OF_HEIGHT

    _add_bilateral_limb(
        robot,
        spec,
        seg_name="upper_arm",
        parent_name="torso",
        parent_offset_z=shoulder_z,
        parent_lateral_y=shoulder_y,
        coord_prefix="shoulder",
        range_min=SHOULDER_FLEXION_MIN,
        range_max=SHOULDER_FLEXION_MAX,
    )

    _ua_mass, ua_len, _ua_rad = _seg(spec, "upper_arm")
    _add_bilateral_limb(
        robot,
        spec,
        seg_name="forearm",
        parent_name="upper_arm",
        parent_offset_z=-ua_len,
        parent_lateral_y=0,
        coord_prefix="elbow",
        range_min=ELBOW_FLEXION_MIN,
        range_max=ELBOW_FLEXION_MAX,
    )

    _fa_mass, fa_len, _fa_rad = _seg(spec, "forearm")
    _add_bilateral_limb(
        robot,
        spec,
        seg_name="hand",
        parent_name="forearm",
        parent_offset_z=-fa_len,
        parent_lateral_y=0,
        coord_prefix="wrist",
        range_min=WRIST_FLEXION_MIN,
        range_max=WRIST_FLEXION_MAX,
    )

    # --- Legs ---
    hip_y = spec.height * HIP_LATERAL_FRAC_OF_HEIGHT

    _add_bilateral_limb(
        robot,
        spec,
        seg_name="thigh",
        parent_name="pelvis",
        parent_offset_z=-p_len / 2.0,
        parent_lateral_y=hip_y,
        coord_prefix="hip",
        range_min=HIP_FLEXION_MIN,
        range_max=HIP_FLEXION_MAX,
    )

    _th_mass, th_len, _th_rad = _seg(spec, "thigh")
    _add_bilateral_limb(
        robot,
        spec,
        seg_name="shank",
        parent_name="thigh",
        parent_offset_z=-th_len,
        parent_lateral_y=0,
        coord_prefix="knee",
        range_min=KNEE_FLEXION_MIN,
        range_max=KNEE_FLEXION_MAX,
    )

    _sh_mass, sh_len, _sh_rad = _seg(spec, "shank")
    _add_bilateral_limb(
        robot,
        spec,
        seg_name="foot",
        parent_name="shank",
        parent_offset_z=-sh_len,
        parent_lateral_y=0,
        coord_prefix="ankle",
        range_min=ANKLE_FLEXION_MIN,
        range_max=ANKLE_FLEXION_MAX,
    )

    return links
