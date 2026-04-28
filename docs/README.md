# Pinocchio Models Documentation

This directory collects architecture notes, simulator conventions, and
repository assessments for `pinocchio-models`.

## Start Here

| Document                                                       | Purpose                                                                   |
| -------------------------------------------------------------- | ------------------------------------------------------------------------- |
| [Architecture diagrams](architecture/model_generation_flow.md) | Component and sequence diagrams for the URDF generation path.             |
| [Joint axis convention](joint_axis_convention.md)              | Coordinate-frame and joint-axis mapping for Pinocchio, Drake, and MuJoCo. |
| [Pinocchio ADR](adr/001-use-pinocchio-for-dynamics.md)         | Decision record for using Pinocchio as the downstream dynamics library.   |
| [Developer Guide](developer_guide.md)                          | Installation, project structure, and contribution workflow.               |

## Architecture Summary

The package generates deterministic URDF XML and leaves Pinocchio runtime setup
to downstream callers. The CLI and public builder functions feed validated
anthropometry and barbell specifications into shared body and barbell builders.
Exercise-specific modules then attach the barbell or fixture and stamp
`initial_position` metadata before the URDF is serialized.

Pinocchio-specific runtime behavior is intentionally outside the generated
URDF:

- callers load the XML with `pin.buildModelFromXML(...)`;
- callers add the floating base with `pin.JointModelFreeFlyer()`;
- callers set gravity programmatically through `model.gravity`;
- callers opt into pose metadata with `get_initial_configuration(...)`.

See [architecture/model_generation_flow.md](architecture/model_generation_flow.md)
for the diagrams behind this flow.
