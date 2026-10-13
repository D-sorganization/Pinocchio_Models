# SPDX-License-Identifier: MIT
"""Cross-engine URDF loading and fingerprinting for MuJoCo and Drake (issue #437).

Provides functions to load Pinocchio_Models URDFs in MuJoCo and Drake,
and compute comparable model fingerprints (total mass, segment masses, joint count).
"""

from __future__ import annotations

import logging
import xml.etree.ElementTree as ET
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

# Canonical human segments in parity standard
EXPECTED_SEGMENTS: tuple[str, ...] = (
    "pelvis",
    "torso",
    "head",
    "upper_arm_l",
    "forearm_l",
    "hand_l",
    "upper_arm_r",
    "forearm_r",
    "hand_r",
    "thigh_l",
    "shank_l",
    "foot_l",
    "thigh_r",
    "shank_r",
    "foot_r",
)

# Minimal inertia value required by MuJoCo for moving bodies
_MIN_INERTIA = "1e-6"


def _find_root_links(root: ET.Element) -> list[str]:
    """Return link names that have no parent joint."""
    child_links: set[str] = set()
    for j in root.findall("joint"):
        child = j.find("child")
        if child is not None:
            c_name = child.get("link")
            if c_name:
                child_links.add(c_name)
    return [
        name
        for link in root.findall("link")
        if (name := link.get("name", "")) and name not in child_links
    ]


def _attach_world_root(root: ET.Element, root_links: list[str]) -> None:
    """Attach a virtual world link and joint if missing."""
    all_links = {link.get("name") for link in root.findall("link")}
    if not root_links or "world" in all_links:
        return

    primary_root = root_links[0]
    world_link = ET.Element("link", {"name": "world"})
    rj_type = "fixed" if primary_root == "bench" else "floating"
    root_joint = ET.Element("joint", {"name": "world_root_joint", "type": rj_type})
    ET.SubElement(root_joint, "parent", {"link": "world"})
    ET.SubElement(root_joint, "child", {"link": primary_root})
    root.insert(0, world_link)
    root.insert(1, root_joint)


def _ensure_minimum_inertias(root: ET.Element) -> None:
    """Ensure non-zero diagonal inertia on all inertial blocks."""
    for link in root.findall("link"):
        inertial = link.find("inertial")
        if inertial is None:
            continue
        inertia = inertial.find("inertia")
        if inertia is None:
            continue
        for axis in ("ixx", "iyy", "izz"):
            if float(inertia.get(axis, 0.0)) <= 1e-12:
                inertia.set(axis, _MIN_INERTIA)


def sanitize_urdf_for_mujoco(urdf_str: str) -> str:
    """Prepare a Pinocchio URDF string so MuJoCo's parser can ingest it cleanly.

    1. Adds a virtual ``world`` link and floating root joint to the root link
       (or fixed joint if the root link is a fixture like ``bench``), preventing
       MuJoCo from absorbing the root segment into the world body.
    2. Ensures moving virtual links have inertia >= mjMINVAL so MuJoCo doesn't
       reject them.
    """
    root = ET.fromstring(urdf_str)  # nosec B314
    root_links = _find_root_links(root)
    _attach_world_root(root, root_links)
    _ensure_minimum_inertias(root)
    return ET.tostring(root, encoding="unicode")


def load_urdf_in_mujoco(urdf_source: str | Path) -> Any:
    """Load a Pinocchio_Models URDF into a real MuJoCo MjModel.

    Args:
        urdf_source: Either a path to a URDF file or a raw URDF XML string.

    Returns:
        The loaded MuJoCo MjModel.
    """
    import mujoco

    if isinstance(urdf_source, Path) or (
        isinstance(urdf_source, str)
        and "\n" not in urdf_source
        and Path(urdf_source).is_file()
    ):
        raw_xml = Path(urdf_source).read_text(encoding="utf-8")
    else:
        raw_xml = str(urdf_source)

    sanitized_xml = sanitize_urdf_for_mujoco(raw_xml)
    return mujoco.MjModel.from_xml_string(sanitized_xml)


def mujoco_fingerprint(model: Any, data: Any | None = None) -> dict[str, Any]:
    """Compute cross-engine fingerprint for a MuJoCo model loaded from URDF."""
    import mujoco

    if data is None:
        data = mujoco.MjData(model)

    mujoco.mj_resetData(model, data)
    mujoco.mj_forward(model, data)

    # Segment masses (filtering out virtual links)
    segment_masses: dict[str, float] = {}
    for b in range(model.nbody):
        bname = model.body(b).name
        if bname in EXPECTED_SEGMENTS:
            segment_masses[bname] = float(model.body_mass[b])

    human_mass = sum(segment_masses.values())
    total_mass = float(sum(model.body_mass))

    # Hinge joints
    hinge_joints: list[str] = [
        model.joint(j).name
        for j in range(model.njnt)
        if model.jnt_type[j] == mujoco.mjtJoint.mjJNT_HINGE
    ]

    return {
        "total_mass_kg": total_mass,
        "human_mass_kg": human_mass,
        "segment_masses_kg": segment_masses,
        "joint_count": len(hinge_joints),
        "joint_names": hinge_joints,
    }


def load_urdf_in_drake(urdf_source: str | Path) -> Any:
    """Load a Pinocchio_Models URDF into Drake MultibodyPlant."""
    from pydrake.multibody.parsing import Parser
    from pydrake.multibody.plant import MultibodyPlant

    if isinstance(urdf_source, Path) or (
        isinstance(urdf_source, str)
        and "\n" not in urdf_source
        and Path(urdf_source).is_file()
    ):
        raw_xml = Path(urdf_source).read_text(encoding="utf-8")
    else:
        raw_xml = str(urdf_source)

    plant = MultibodyPlant(time_step=0.0)
    parser = Parser(plant)
    parser.AddModelsFromString(raw_xml, "urdf")
    plant.Finalize()
    return plant


def drake_fingerprint(plant: Any) -> dict[str, Any]:
    """Compute cross-engine fingerprint for a Drake MultibodyPlant loaded from URDF."""
    context = plant.CreateDefaultContext()
    total_mass = float(plant.CalcTotalMass(context))

    # 1-DOF joints
    joints_1dof: list[str] = []
    for ji in plant.GetJointIndices():
        joint = plant.get_joint(ji)
        if joint.num_positions() == 1:
            joints_1dof.append(joint.name())

    segment_masses: dict[str, float] = {}
    for bi in plant.GetBodyIndices():
        body = plant.get_body(bi)
        bname = body.name()
        if bname in EXPECTED_SEGMENTS:
            segment_masses[bname] = float(body.default_mass())

    return {
        "total_mass_kg": total_mass,
        "segment_masses_kg": segment_masses,
        "joint_count": len(joints_1dof),
        "joint_names": joints_1dof,
    }


def urdf_expected_fingerprint(urdf_str: str) -> dict[str, Any]:
    """Parse URDF XML directly to extract expected masses and joint counts."""
    root = ET.fromstring(urdf_str)  # nosec B314 -- urdf is trusted internal XML

    segment_masses: dict[str, float] = {}
    total_mass = 0.0

    for link in root.findall("link"):
        lname = link.get("name", "")
        inertial = link.find("inertial")
        if inertial is not None:
            mass_el = inertial.find("mass")
            if mass_el is not None:
                mass_val = float(mass_el.get("value", 0.0))
                total_mass += mass_val
                if lname in EXPECTED_SEGMENTS:
                    segment_masses[lname] = mass_val

    revolute_joints: list[str] = [
        j.get("name", "") for j in root.findall("joint") if j.get("type") == "revolute"
    ]

    return {
        "total_mass_kg": total_mass,
        "segment_masses_kg": segment_masses,
        "joint_count": len(revolute_joints),
        "joint_names": revolute_joints,
    }
