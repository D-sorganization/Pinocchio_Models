"""URDF XML generation helpers for Pinocchio models.

DRY: All links, joints, and geometry share these formatting functions
so that URDF structure is defined in exactly one place.

Convention: Z-up, forward is X. Standard URDF format compatible
with Pinocchio, RViz, and Gazebo.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET


def vec3_str(x: float, y: float, z: float) -> str:
    """Format three floats as a space-separated string for URDF XML."""
    return f"{x:.6f} {y:.6f} {z:.6f}"


def add_link(
    robot: ET.Element,
    *,
    name: str,
    mass: float,
    origin_xyz: tuple[float, float, float] = (0, 0, 0),
    origin_rpy: tuple[float, float, float] = (0, 0, 0),
    ixx: float,
    iyy: float,
    izz: float,
    ixy: float = 0.0,
    ixz: float = 0.0,
    iyz: float = 0.0,
    visual_geometry: ET.Element | None = None,
    collision_geometry: ET.Element | None = None,
) -> ET.Element:
    """Append a <link> element with <inertial>, optional <visual>/<collision>."""
    link = ET.SubElement(robot, "link", name=name)

    # Inertial
    inertial = ET.SubElement(link, "inertial")
    ET.SubElement(
        inertial,
        "origin",
        xyz=vec3_str(*origin_xyz),
        rpy=vec3_str(*origin_rpy),
    )
    ET.SubElement(inertial, "mass", value=f"{mass:.6f}")
    ET.SubElement(
        inertial,
        "inertia",
        ixx=f"{ixx:.6f}",
        iyy=f"{iyy:.6f}",
        izz=f"{izz:.6f}",
        ixy=f"{ixy:.6f}",
        ixz=f"{ixz:.6f}",
        iyz=f"{iyz:.6f}",
    )

    if visual_geometry is not None:
        visual = ET.SubElement(link, "visual")
        ET.SubElement(visual, "origin", xyz="0 0 0", rpy="0 0 0")
        visual.append(visual_geometry)

    if collision_geometry is not None:
        collision = ET.SubElement(link, "collision")
        ET.SubElement(collision, "origin", xyz="0 0 0", rpy="0 0 0")
        collision.append(collision_geometry)

    return link


def add_revolute_joint(
    robot: ET.Element,
    *,
    name: str,
    parent: str,
    child: str,
    origin_xyz: tuple[float, float, float] = (0, 0, 0),
    origin_rpy: tuple[float, float, float] = (0, 0, 0),
    axis: tuple[float, float, float] = (0, 0, 1),
    lower: float = -1.5708,
    upper: float = 1.5708,
    effort: float = 1000.0,
    velocity: float = 10.0,
) -> ET.Element:
    """Append a <joint type='revolute'> to *robot*."""
    joint = ET.SubElement(robot, "joint", name=name, type="revolute")
    ET.SubElement(
        joint,
        "origin",
        xyz=vec3_str(*origin_xyz),
        rpy=vec3_str(*origin_rpy),
    )
    ET.SubElement(joint, "parent", link=parent)
    ET.SubElement(joint, "child", link=child)
    ET.SubElement(joint, "axis", xyz=vec3_str(*axis))
    ET.SubElement(
        joint,
        "limit",
        lower=f"{lower:.6f}",
        upper=f"{upper:.6f}",
        effort=f"{effort:.1f}",
        velocity=f"{velocity:.1f}",
    )
    return joint


def add_fixed_joint(
    robot: ET.Element,
    *,
    name: str,
    parent: str,
    child: str,
    origin_xyz: tuple[float, float, float] = (0, 0, 0),
    origin_rpy: tuple[float, float, float] = (0, 0, 0),
) -> ET.Element:
    """Append a <joint type='fixed'> (weld) to *robot*."""
    joint = ET.SubElement(robot, "joint", name=name, type="fixed")
    ET.SubElement(
        joint,
        "origin",
        xyz=vec3_str(*origin_xyz),
        rpy=vec3_str(*origin_rpy),
    )
    ET.SubElement(joint, "parent", link=parent)
    ET.SubElement(joint, "child", link=child)
    return joint


def add_continuous_joint(
    robot: ET.Element,
    *,
    name: str,
    parent: str,
    child: str,
    origin_xyz: tuple[float, float, float] = (0, 0, 0),
    origin_rpy: tuple[float, float, float] = (0, 0, 0),
    axis: tuple[float, float, float] = (0, 0, 1),
    effort: float = 1000.0,
    velocity: float = 10.0,
) -> ET.Element:
    """Append a <joint type='continuous'> (unlimited rotation) to *robot*."""
    joint = ET.SubElement(robot, "joint", name=name, type="continuous")
    ET.SubElement(
        joint,
        "origin",
        xyz=vec3_str(*origin_xyz),
        rpy=vec3_str(*origin_rpy),
    )
    ET.SubElement(joint, "parent", link=parent)
    ET.SubElement(joint, "child", link=child)
    ET.SubElement(joint, "axis", xyz=vec3_str(*axis))
    ET.SubElement(
        joint,
        "limit",
        effort=f"{effort:.1f}",
        velocity=f"{velocity:.1f}",
    )
    return joint


def make_cylinder_geometry(radius: float, length: float) -> ET.Element:
    """Create a <geometry><cylinder> element."""
    geom = ET.Element("geometry")
    ET.SubElement(geom, "cylinder", radius=f"{radius:.6f}", length=f"{length:.6f}")
    return geom


def make_box_geometry(x: float, y: float, z: float) -> ET.Element:
    """Create a <geometry><box> element."""
    geom = ET.Element("geometry")
    ET.SubElement(geom, "box", size=vec3_str(x, y, z))
    return geom


def make_sphere_geometry(radius: float) -> ET.Element:
    """Create a <geometry><sphere> element."""
    geom = ET.Element("geometry")
    ET.SubElement(geom, "sphere", radius=f"{radius:.6f}")
    return geom


def serialize_model(root: ET.Element) -> str:
    """Serialize a URDF robot ElementTree to a formatted XML string."""
    ET.indent(root, space="  ")
    return ET.tostring(root, encoding="unicode", xml_declaration=True)
