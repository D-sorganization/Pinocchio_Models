"""URDF/Pinocchio assembly for the full-body model.

Builds the complete robot XML tree by orchestrating the anthropometric helpers
defined in ``body_anthropometrics``.  Exercise modules should call
``create_full_body()`` and operate on the returned link dict; they should never
manipulate segment internals (Law of Demeter).

Segments (bilateral where noted):
  pelvis, torso, head,
  upper_arm_{l,r}, forearm_{l,r}, hand_{l,r},
  thigh_{l,r}, shank_{l,r}, foot_{l,r}

Multi-DOF joints (compound revolute joints via virtual links):
  pelvis is the root link (Pinocchio adds FreeFlyer programmatically),
  lumbar — 3-DOF: flex (X), lateral (Z), rotate (Y)
  neck (revolute — 1-DOF flexion about Y)
  shoulder_{l,r} — 3-DOF: flex (X), adduct (Z), rotate (Y)
  elbow_{l,r} (revolute — 1-DOF flexion about Y)
  wrist_{l,r} — 2-DOF: flex (Y), deviate (Z)
  hip_{l,r} — 3-DOF: flex (X), adduct (Z), rotate (Y)
  knee_{l,r} (revolute — 1-DOF flexion about Y)
  ankle_{l,r} — 2-DOF: flex (Y), invert (X)

Convention: Z-up (vertical), X-forward. Pinocchio adds the floating
base programmatically via pin.JointModelFreeFlyer().

Joint axis convention note (issue #65):
  Simple revolute joints (knee, elbow, ankle) use **Y-axis** for
  sagittal-plane flexion.  Drake and MuJoCo often use **X-axis** for
  the same motion.  See ``docs/joint_axis_convention.md`` for the full
  mapping and porting guidance.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET

from pinocchio_models.shared.body.body_anthropometrics import (
    _BILATERAL_SEGMENTS,  # noqa: F401 -- re-exported for internal use
    _SEGMENT_TABLE,  # noqa: F401 -- re-exported for internal use
    BodyModelSpec,
    _add_bilateral_limb_simple,
    _add_bilateral_ndof,
    _seg,
)
from pinocchio_models.shared.constants import (
    ANKLE_FLEXION_MAX,
    ANKLE_FLEXION_MIN,
    ANKLE_INVERSION_MAX,
    ANKLE_INVERSION_MIN,
    ELBOW_FLEXION_MAX,
    ELBOW_FLEXION_MIN,
    HIP_ADDUCTION_MAX,
    HIP_ADDUCTION_MIN,
    HIP_FLEXION_MAX,
    HIP_FLEXION_MIN,
    HIP_LATERAL_FRAC_OF_HEIGHT,
    HIP_ROTATION_MAX,
    HIP_ROTATION_MIN,
    KNEE_FLEXION_MAX,
    KNEE_FLEXION_MIN,
    LUMBAR_FLEXION_MAX,
    LUMBAR_FLEXION_MIN,
    LUMBAR_LATERAL_MAX,
    LUMBAR_LATERAL_MIN,
    LUMBAR_ROTATION_MAX,
    LUMBAR_ROTATION_MIN,
    NECK_FLEXION_MAX,
    NECK_FLEXION_MIN,
    SHOULDER_ADDUCTION_MAX,
    SHOULDER_ADDUCTION_MIN,
    SHOULDER_FLEXION_MAX,
    SHOULDER_FLEXION_MIN,
    SHOULDER_HEIGHT_FRAC,
    SHOULDER_LATERAL_FRAC_OF_HEIGHT,
    SHOULDER_ROTATION_MAX,
    SHOULDER_ROTATION_MIN,
    WRIST_DEVIATION_MAX,
    WRIST_DEVIATION_MIN,
    WRIST_FLEXION_MAX,
    WRIST_FLEXION_MIN,
)
from pinocchio_models.shared.utils.geometry import (
    cylinder_inertia,
    rectangular_prism_inertia,
)
from pinocchio_models.shared.utils.urdf_helpers import (
    add_link,
    add_revolute_joint,
    add_virtual_link,
    make_box_geometry,
)

__all__ = ["BodyModelSpec", "create_full_body"]


def _build_axial_chain(
    robot: ET.Element,
    spec: BodyModelSpec,
    links: dict[str, ET.Element],
) -> tuple[float, float]:
    """Stage 1: Build pelvis, torso (3-DOF lumbar), and head.

    Returns (pelvis_length, torso_length) needed by downstream stages.
    """
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

    # --- Torso (3-DOF lumbar: flex, lateral, rotate) ---
    t_mass, t_len, t_rad = _seg(spec, "torso")
    t_inertia = rectangular_prism_inertia(t_mass, t_rad * 2, t_len, t_rad * 2)

    add_virtual_link(robot, name="lumbar_virtual_1")
    add_revolute_joint(
        robot,
        name="lumbar_flex",
        parent="pelvis",
        child="lumbar_virtual_1",
        origin_xyz=(0, 0, p_len / 2.0),
        axis=(1, 0, 0),
        lower=LUMBAR_FLEXION_MIN,
        upper=LUMBAR_FLEXION_MAX,
    )

    add_virtual_link(robot, name="lumbar_virtual_2")
    add_revolute_joint(
        robot,
        name="lumbar_lateral",
        parent="lumbar_virtual_1",
        child="lumbar_virtual_2",
        origin_xyz=(0, 0, 0),
        axis=(0, 0, 1),
        lower=LUMBAR_LATERAL_MIN,
        upper=LUMBAR_LATERAL_MAX,
    )

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
        name="lumbar_rotate",
        parent="lumbar_virtual_2",
        child="torso",
        origin_xyz=(0, 0, 0),
        axis=(0, 1, 0),
        lower=LUMBAR_ROTATION_MIN,
        upper=LUMBAR_ROTATION_MAX,
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

    return p_len, t_len


def _build_upper_limbs(
    robot: ET.Element,
    spec: BodyModelSpec,
    torso_length: float,
) -> None:
    """Stage 2: Build bilateral arms -- shoulder, elbow, wrist."""
    shoulder_z = torso_length * SHOULDER_HEIGHT_FRAC
    shoulder_y = spec.height * SHOULDER_LATERAL_FRAC_OF_HEIGHT

    _add_bilateral_ndof(
        robot,
        spec,
        seg_name="upper_arm",
        parent_name="torso",
        parent_offset_z=shoulder_z,
        parent_lateral_y=shoulder_y,
        coord_prefix="shoulder",
        joints=[
            ("flex", (1, 0, 0), SHOULDER_FLEXION_MIN, SHOULDER_FLEXION_MAX),
            ("adduct", (0, 0, 1), SHOULDER_ADDUCTION_MIN, SHOULDER_ADDUCTION_MAX),
            ("rotate", (0, 1, 0), SHOULDER_ROTATION_MIN, SHOULDER_ROTATION_MAX),
        ],
    )

    _ua_mass, ua_len, _ua_rad = _seg(spec, "upper_arm")
    _add_bilateral_limb_simple(
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
    _add_bilateral_ndof(
        robot,
        spec,
        seg_name="hand",
        parent_name="forearm",
        parent_offset_z=-fa_len,
        parent_lateral_y=0,
        coord_prefix="wrist",
        joints=[
            ("flex", (0, 1, 0), WRIST_FLEXION_MIN, WRIST_FLEXION_MAX),
            ("deviate", (0, 0, 1), WRIST_DEVIATION_MIN, WRIST_DEVIATION_MAX),
        ],
    )


def _build_lower_limbs(
    robot: ET.Element,
    spec: BodyModelSpec,
    pelvis_length: float,
) -> None:
    """Stage 3: Build bilateral legs -- hip, knee, ankle, foot collision."""
    hip_y = spec.height * HIP_LATERAL_FRAC_OF_HEIGHT

    _add_bilateral_ndof(
        robot,
        spec,
        seg_name="thigh",
        parent_name="pelvis",
        parent_offset_z=-pelvis_length / 2.0,
        parent_lateral_y=hip_y,
        coord_prefix="hip",
        joints=[
            ("flex", (1, 0, 0), HIP_FLEXION_MIN, HIP_FLEXION_MAX),
            ("adduct", (0, 0, 1), HIP_ADDUCTION_MIN, HIP_ADDUCTION_MAX),
            ("rotate", (0, 1, 0), HIP_ROTATION_MIN, HIP_ROTATION_MAX),
        ],
    )

    _th_mass, th_len, _th_rad = _seg(spec, "thigh")
    _add_bilateral_limb_simple(
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
    _add_bilateral_ndof(
        robot,
        spec,
        seg_name="foot",
        parent_name="shank",
        parent_offset_z=-sh_len,
        parent_lateral_y=0,
        coord_prefix="ankle",
        joints=[
            ("flex", (0, 1, 0), ANKLE_FLEXION_MIN, ANKLE_FLEXION_MAX),
            ("invert", (1, 0, 0), ANKLE_INVERSION_MIN, ANKLE_INVERSION_MAX),
        ],
    )

    # Foot collision geometry (sole contact box)
    # Dimensions: 0.26 x 0.10 x 0.02 m, centered 0.01 m below frame origin.
    _SOLE_COLLISION_DIMS = (0.26, 0.10, 0.02)
    for side in ("l", "r"):
        foot_link = robot.find(f".//link[@name='foot_{side}']")
        if foot_link is not None:
            collision = ET.SubElement(foot_link, "collision")
            ET.SubElement(collision, "origin", xyz="0 0 -0.01", rpy="0 0 0")
            collision.append(make_box_geometry(*_SOLE_COLLISION_DIMS))


def create_full_body(
    robot: ET.Element,
    spec: BodyModelSpec | None = None,
) -> dict[str, ET.Element]:
    """Build the full-body model and append links/joints to the <robot>.

    The pelvis is the root link. Pinocchio adds the floating base
    programmatically via pin.JointModelFreeFlyer() when loading URDF.

    Multi-DOF joints use intermediate virtual (zero-mass) links to
    chain sequential revolute joints, as required by URDF's tree topology.

    Internally delegates to three staged builders:
      1. ``_build_axial_chain`` -- pelvis, torso (lumbar), head
      2. ``_build_upper_limbs`` -- shoulders, elbows, wrists
      3. ``_build_lower_limbs`` -- hips, knees, ankles, foot collision

    Returns dict of link name -> ET.Element for all created links.
    """
    if spec is None:
        spec = BodyModelSpec()

    links: dict[str, ET.Element] = {}

    pelvis_length, torso_length = _build_axial_chain(robot, spec, links)
    _build_upper_limbs(robot, spec, torso_length)
    _build_lower_limbs(robot, spec, pelvis_length)

    return links
