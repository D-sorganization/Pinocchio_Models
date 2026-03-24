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
    data  = model.createData()

    q0 = get_initial_configuration(model, urdf_str)
    pin.forwardKinematics(model, data, q0)
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


def set_joint_default(robot: ET.Element, prefix: str, value: float) -> None:
    """Set the ``initial_position`` metadata attribute on matching joints.

    Iterates over all ``<joint>`` children of *robot* and stamps an
    ``initial_position`` attribute on every joint whose ``name`` equals
    *prefix* **or** starts with ``"{prefix}_"``.

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
    """
    for joint in robot.findall("joint"):
        name = joint.get("name", "")
        if name == prefix or name.startswith(f"{prefix}_"):
            joint.set("initial_position", f"{value:.6f}")


def get_initial_configuration(model: object, xml_str: str) -> object:
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
        data  = model.createData()

        q0 = get_initial_configuration(model, urdf_str)
        pin.forwardKinematics(model, data, q0)
    """
    try:
        import pinocchio as pin
    except ImportError as exc:
        raise ImportError(
            "pinocchio and numpy are required for get_initial_configuration. "
            "Install with: pip install pinocchio-models[all-addons]"
        ) from exc

    q = pin.neutral(model)

    root = ET.fromstring(xml_str)
    for joint_el in root.findall("joint"):
        initial_pos_str = joint_el.get("initial_position")
        if initial_pos_str is None:
            continue
        joint_name = joint_el.get("name", "")
        try:
            joint_id = model.getJointId(joint_name)
        except Exception:
            continue
        if joint_id >= len(model.joints):
            continue
        joint = model.joints[joint_id]
        idx_q = joint.idx_q
        nq_j = joint.nq
        if nq_j == 1:
            q[idx_q] = float(initial_pos_str)

    return q
