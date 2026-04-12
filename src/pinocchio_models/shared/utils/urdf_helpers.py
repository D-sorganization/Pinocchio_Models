"""URDF XML generation helpers for Pinocchio models.

DRY: All links, joints, and geometry share these formatting functions
so that URDF structure is defined in exactly one place.

Convention: Z-up, forward is X. Standard URDF format compatible
with Pinocchio, RViz, and Gazebo.

Initial-pose metadata
---------------------
The ``initial_position`` XML attribute written by :func:`set_joint_default`
is **metadata only**.  Pinocchio does *not* read it when loading URDF; it
simply ignores unknown joint attributes.  The attribute documents the
intended starting configuration for human readers and downstream tooling.

To apply an initial pose at runtime use :func:`get_initial_configuration`,
which reads those attributes back and returns a numpy array compatible with
``pin.forwardKinematics`` / ``pin.computeJointJacobians``, etc.  Example::

    import pinocchio as pin
    from pinocchio_models.exercises.squat.squat_model import build_squat_model
    from pinocchio_models.shared.utils.urdf_helpers import get_initial_configuration

    urdf_str = build_squat_model()
    model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
    data = model.createData()

    q0 = get_initial_configuration(model, urdf_str)
    pin.forwardKinematics(model, data, q0)
"""

from __future__ import annotations

import logging
import math
import xml.etree.ElementTree as ET
from typing import Any

logger = logging.getLogger(__name__)


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
    visual_origin_rpy: tuple[float, float, float] = (0.0, 0.0, 0.0),
    collision_geometry: ET.Element | None = None,
) -> ET.Element:
    """Append a <link> element with <inertial>, optional <visual>/<collision>.

    Parameters
    ----------
    visual_origin_rpy:
        Roll-pitch-yaw for the visual geometry origin. Use ``(math.pi/2, 0, 0)``
        to rotate a cylinder from its default Z-axis orientation to lie along Y.
    """
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
        ET.SubElement(
            visual,
            "origin",
            xyz="0 0 0",
            rpy=vec3_str(*visual_origin_rpy),
        )
        visual.append(visual_geometry)

    if collision_geometry is not None:
        collision = ET.SubElement(link, "collision")
        ET.SubElement(collision, "origin", xyz="0 0 0", rpy="0 0 0")
        collision.append(collision_geometry)

    return link


def add_virtual_link(
    robot: ET.Element,
    *,
    name: str,
) -> ET.Element:
    """Append a zero-mass virtual link for compound (multi-DOF) joints.

    URDF requires every joint to connect two distinct links. To model
    a multi-DOF anatomical joint (e.g., 3-DOF hip) we chain sequential
    revolute joints with virtual (massless) links between them.

    URDF also requires non-zero mass, so we use a negligible mass
    (1e-6 kg) and tiny inertia (1e-9 kg*m^2 on each principal axis).
    """
    return add_link(
        robot,
        name=name,
        mass=1e-6,
        origin_xyz=(0, 0, 0),
        ixx=1e-9,
        iyy=1e-9,
        izz=1e-9,
    )


def add_revolute_joint(
    robot: ET.Element,
    *,
    name: str,
    parent: str,
    child: str,
    origin_xyz: tuple[float, float, float] = (0, 0, 0),
    origin_rpy: tuple[float, float, float] = (0, 0, 0),
    axis: tuple[float, float, float] = (0, 0, 1),
    lower: float = -math.pi / 2,
    upper: float = math.pi / 2,
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


def set_joint_default(
    robot: ET.Element,
    prefix: str,
    value: float,
    *,
    exact_suffix: str | None = None,
) -> None:
    """Set the ``initial_position`` metadata attribute on matching joints.

    Iterates over all ``<joint>`` children of *robot* and stamps an
    ``initial_position`` attribute on every joint whose ``name`` equals
    *prefix* **or** starts with ``"{prefix}_"``.

    When *exact_suffix* is provided, only joints whose name ends with
    that suffix are matched. This is useful for multi-DOF compound joints
    where, e.g., only the ``_flex`` component should receive the initial
    angle while ``_adduct`` and ``_rotate`` remain at zero.

    .. important::
        This attribute is **metadata only**.  Pinocchio does *not* read it
        when loading URDF; the value has no effect on simulation unless
        consumed explicitly via :func:`get_initial_configuration`.

    Parameters
    ----------
    robot:
        Root ``<robot>`` XML element produced by the exercise builder.
    prefix:
        Joint-name prefix, e.g. ``"hip"`` matches ``hip_l`` and ``hip_r``.
    value:
        Angle in radians to record as the default position.
    exact_suffix:
        If given, only match joints whose name ends with this suffix.
        E.g. ``exact_suffix="_flex"`` with ``prefix="hip"`` matches
        ``hip_l_flex`` and ``hip_r_flex`` but not ``hip_l_adduct``.
    """
    for joint in robot.findall("joint"):
        name = joint.get("name", "")
        if name == prefix or name.startswith(f"{prefix}_"):
            if exact_suffix is not None and not name.endswith(exact_suffix):
                continue
            joint.set("initial_position", f"{value:.6f}")


def _import_pinocchio() -> Any:
    """Import and return the ``pinocchio`` module, with a clear error message."""
    try:
        import pinocchio as pin
    except ImportError as exc:
        raise ImportError(
            "pinocchio and numpy are required for get_initial_configuration. "
            "Install with: pip install pinocchio-models[all-addons]"
        ) from exc
    return pin


def _parse_initial_positions(xml_str: str) -> list[tuple[str, float]]:
    """Extract ``(joint_name, initial_position)`` pairs from URDF metadata."""
    root = ET.fromstring(xml_str)  # nosec B314 -- xml_str is internally generated URDF
    pairs: list[tuple[str, float]] = []
    for joint_el in root.findall("joint"):
        initial_pos_str = joint_el.get("initial_position")
        if initial_pos_str is None:
            continue
        joint_name = joint_el.get("name", "")
        pairs.append((joint_name, float(initial_pos_str)))
    return pairs


def _apply_initial_positions(
    model: Any, q: Any, initial_positions: list[tuple[str, float]]
) -> None:
    """Write each ``(name, value)`` pair onto the matching DOF index of *q*."""
    for joint_name, value in initial_positions:
        try:
            joint_id = model.getJointId(joint_name)
        except (RuntimeError, KeyError) as _e:
            logger.warning("Joint %s not found in model: %s", joint_name, _e)
            continue
        if joint_id >= len(model.joints):
            continue
        joint = model.joints[joint_id]
        if joint.nq == 1:
            q[joint.idx_q] = value


def get_initial_configuration(model: Any, xml_str: str) -> Any:
    """Build a Pinocchio configuration vector from ``initial_position`` metadata.

    Reads the ``initial_position`` attributes written by
    :func:`set_joint_default` and maps them onto the corresponding DOF
    indices in *model*.  Joints without an ``initial_position`` attribute
    receive the value from ``pin.neutral(model)``.

    This is the **correct way** to apply an initial pose with Pinocchio —
    read the metadata from the URDF string, then pass the resulting array
    to ``pin.forwardKinematics``.

    Parameters
    ----------
    model:
        A ``pinocchio.Model`` built from the same URDF string, typically via::

            model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())

    xml_str:
        The URDF XML string (as returned by ``ExerciseModelBuilder.build()``).

    Returns
    -------
    numpy.ndarray
        Configuration vector of shape ``(model.nq,)`` with FreeFlyer DOFs
        at neutral and actuated joints set to their ``initial_position``
        values.

    Raises
    ------
    ImportError
        If ``pinocchio`` or ``numpy`` are not installed.

    Example
    -------
    ::

        import pinocchio as pin
        from pinocchio_models.exercises.squat.squat_model import build_squat_model
        from pinocchio_models.shared.utils.urdf_helpers import get_initial_configuration

        urdf_str = build_squat_model()
        model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
        data = model.createData()

        q0 = get_initial_configuration(model, urdf_str)
        pin.forwardKinematics(model, data, q0)
    """
    pin = _import_pinocchio()
    q = pin.neutral(model)
    initial_positions = _parse_initial_positions(xml_str)
    _apply_initial_positions(model, q, initial_positions)
    return q
