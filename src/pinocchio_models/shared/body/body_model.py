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
  lumbar — 3-DOF: flex, lateral, rotate
  neck (revolute — 1-DOF flexion)
  shoulder_{l,r} — 3-DOF: flex, adduct, rotate
  elbow_{l,r} (revolute — 1-DOF flexion)
  wrist_{l,r} — 2-DOF: flex, deviate
  hip_{l,r} — 3-DOF: flex, adduct, rotate
  knee_{l,r} (revolute — 1-DOF flexion)
  ankle_{l,r} — 2-DOF: flex, invert

Convention (issue #435): the cross-repo parity standard's canonical frame,
Z-up, X forward, Y LEFT (left segments at +Y, right at -Y). Every joint frame
is aligned with the world at q=0, so each ``<axis>`` literal is the canonical
axis of its coordinate (flexion about -Y, adduction about +X on the right and
-X on the left, ...). Axes and joint origins are read from the vendored
standard (``canonical_topology``), never written as literals. Pinocchio adds
the floating base programmatically via pin.JointModelFreeFlyer().

See ``docs/joint_axis_convention.md`` for the mapping and porting guidance.
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
from pinocchio_models.shared.body.canonical_topology import joint_axis, joint_offset
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
) -> None:
    """Stage 1: Build pelvis, torso (3-DOF lumbar), and head."""
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
        origin_xyz=joint_offset("torso", spec.height),
        axis=joint_axis("lumbar_flex"),
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
        axis=joint_axis("lumbar_lateral"),
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
        axis=joint_axis("lumbar_rotate"),
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
        origin_xyz=joint_offset("head", spec.height),
        axis=joint_axis("neck_flex"),
        lower=NECK_FLEXION_MIN,
        upper=NECK_FLEXION_MAX,
    )


def _add_limb_chain(
    robot: ET.Element,
    spec: BodyModelSpec,
    *,
    seg_name: str,
    parent_name: str,
    coord_prefix: str,
    joints: list[tuple[str, float, float]] | None = None,
    limits: tuple[float, float] = (0.0, 0.0),
) -> None:
    """Add one bilateral segment at its standard joint origin.

    The origin comes from the parity standard (left = +Y); *joints* gives the
    (suffix, min, max) of an N-DOF compound joint, otherwise a single flexion
    joint with *limits* is used.
    """
    _x, lateral, vertical = joint_offset(f"{seg_name}_l", spec.height)
    if joints is None:
        _add_bilateral_limb_simple(
            robot,
            spec,
            seg_name=seg_name,
            parent_name=parent_name,
            parent_offset_z=vertical,
            parent_lateral_y=lateral,
            coord_prefix=coord_prefix,
            range_min=limits[0],
            range_max=limits[1],
        )
        return
    _add_bilateral_ndof(
        robot,
        spec,
        seg_name=seg_name,
        parent_name=parent_name,
        parent_offset_z=vertical,
        parent_lateral_y=lateral,
        coord_prefix=coord_prefix,
        joints=joints,
    )


def _build_upper_limbs(robot: ET.Element, spec: BodyModelSpec) -> None:
    """Stage 2: Build bilateral arms -- shoulder, elbow, wrist."""
    _add_limb_chain(
        robot,
        spec,
        seg_name="upper_arm",
        parent_name="torso",
        coord_prefix="shoulder",
        joints=[
            ("flex", SHOULDER_FLEXION_MIN, SHOULDER_FLEXION_MAX),
            ("adduct", SHOULDER_ADDUCTION_MIN, SHOULDER_ADDUCTION_MAX),
            ("rotate", SHOULDER_ROTATION_MIN, SHOULDER_ROTATION_MAX),
        ],
    )
    _add_limb_chain(
        robot,
        spec,
        seg_name="forearm",
        parent_name="upper_arm",
        coord_prefix="elbow",
        limits=(ELBOW_FLEXION_MIN, ELBOW_FLEXION_MAX),
    )
    _add_limb_chain(
        robot,
        spec,
        seg_name="hand",
        parent_name="forearm",
        coord_prefix="wrist",
        joints=[
            ("flex", WRIST_FLEXION_MIN, WRIST_FLEXION_MAX),
            ("deviate", WRIST_DEVIATION_MIN, WRIST_DEVIATION_MAX),
        ],
    )


def _add_foot_collision(
    robot: ET.Element,
    side: str,
    dims: tuple[float, float, float],
) -> None:
    """Attach sole contact-box collision geometry for the given side.

    Args:
        robot: The root ``<robot>`` XML element.
        side: ``'l'`` or ``'r'``.
        dims: ``(length, width, height)`` of the sole contact box in metres.
    """
    target_name = f"foot_{side}"
    foot_link = None
    for link in reversed(robot):
        if link.tag == "link" and link.get("name") == target_name:
            foot_link = link
            break

    if foot_link is not None:
        collision = ET.SubElement(foot_link, "collision")
        ET.SubElement(collision, "origin", {"xyz": "0 0 -0.01", "rpy": "0 0 0"})
        collision.append(make_box_geometry(*dims))


def _build_lower_limbs(robot: ET.Element, spec: BodyModelSpec) -> None:
    """Stage 3: Build bilateral legs -- hip, knee, ankle, foot collision."""
    _add_limb_chain(
        robot,
        spec,
        seg_name="thigh",
        parent_name="pelvis",
        coord_prefix="hip",
        joints=[
            ("flex", HIP_FLEXION_MIN, HIP_FLEXION_MAX),
            ("adduct", HIP_ADDUCTION_MIN, HIP_ADDUCTION_MAX),
            ("rotate", HIP_ROTATION_MIN, HIP_ROTATION_MAX),
        ],
    )
    _add_limb_chain(
        robot,
        spec,
        seg_name="shank",
        parent_name="thigh",
        coord_prefix="knee",
        limits=(KNEE_FLEXION_MIN, KNEE_FLEXION_MAX),
    )
    _add_limb_chain(
        robot,
        spec,
        seg_name="foot",
        parent_name="shank",
        coord_prefix="ankle",
        joints=[
            ("flex", ANKLE_FLEXION_MIN, ANKLE_FLEXION_MAX),
            ("invert", ANKLE_INVERSION_MIN, ANKLE_INVERSION_MAX),
        ],
    )

    _SOLE_COLLISION_DIMS = (0.26, 0.10, 0.02)
    for side in ("l", "r"):
        _add_foot_collision(robot, side, _SOLE_COLLISION_DIMS)


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

    _build_axial_chain(robot, spec, links)
    _build_upper_limbs(robot, spec)
    _build_lower_limbs(robot, spec)

    return links
