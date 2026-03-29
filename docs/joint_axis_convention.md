# Joint Axis Convention: Pinocchio Models vs Drake/MuJoCo

## This Project's Convention (Y-axis sagittal-plane joints)

Pinocchio Models uses the **URDF standard** joint axis assignments:

| Joint | Axis | Plane | Notes |
|-------|------|-------|-------|
| Hip flexion/extension | **X** `(1,0,0)` | Sagittal | About medio-lateral axis |
| Hip adduction/abduction | **Z** `(0,0,1)` | Frontal | About vertical axis |
| Hip rotation | **Y** `(0,1,0)` | Transverse | About long axis of femur |
| Knee flexion/extension | **Y** `(0,1,0)` | Sagittal | Single-DOF revolute |
| Ankle dorsi/plantarflexion | **Y** `(0,1,0)` | Sagittal | Single-DOF revolute |
| Ankle inversion/eversion | **X** `(1,0,0)` | Frontal | About longitudinal foot axis |
| Shoulder flexion/extension | **X** `(1,0,0)` | Sagittal | About medio-lateral axis |
| Shoulder adduction/abduction | **Z** `(0,0,1)` | Frontal | |
| Shoulder rotation | **Y** `(0,1,0)` | Transverse | |
| Elbow flexion | **Y** `(0,1,0)` | Sagittal | Single-DOF revolute |
| Lumbar flexion | **X** `(1,0,0)` | Sagittal | |
| Lumbar lateral bend | **Z** `(0,0,1)` | Frontal | |
| Lumbar rotation | **Y** `(0,1,0)` | Transverse | |
| Neck flexion | **Y** `(0,1,0)` | Sagittal | |
| Wrist flexion | **Y** `(0,1,0)` | Sagittal | |
| Wrist deviation | **Z** `(0,0,1)` | Frontal | |

### Coordinate frame

- **Z-up** (vertical)
- **X-forward** (anterior direction)
- **Y-left** (medio-lateral, completing right-hand rule)

## Drake / MuJoCo Convention (X-axis sagittal-plane joints)

Drake and MuJoCo commonly use **X-axis** for sagittal-plane
flexion/extension on simple revolute joints (knee, elbow, ankle).
This is because their default body frames often orient the long axis of
the limb segment along Z, making X the natural medio-lateral axis.

| Joint | Drake/MuJoCo Axis | This Project Axis |
|-------|------------------|-------------------|
| Knee flexion | X `(1,0,0)` | Y `(0,1,0)` |
| Elbow flexion | X `(1,0,0)` | Y `(0,1,0)` |
| Ankle flexion | X `(1,0,0)` | Y `(0,1,0)` |

## Why the Difference?

The axis choice depends on the body-frame orientation convention:

1. **This project** follows the URDF/Pinocchio convention where limb
   segments have their long axis along Z (the cylinder axis) and
   sagittal-plane flexion occurs about Y.

2. **Drake/MuJoCo** models sometimes orient limb segments along Y or
   use a different body-frame convention where X becomes the
   medio-lateral axis.

**Both conventions are physically correct** -- they produce the same
motion when the body-frame orientation is accounted for.

## Porting Between Simulators

When transferring joint configurations between Pinocchio and
Drake/MuJoCo:

1. **Identify the joint axis** in both models (check `<axis xyz="..."/>`
   in URDF vs the joint definition in MJCF/SDF).
2. **Joint angles are invariant** -- the same angle value produces the
   same physical rotation regardless of which axis label is used,
   provided the axis vectors are equivalent in the world frame.
3. **Multi-DOF joints** (hip, shoulder, lumbar) may have different
   decomposition orders. This project uses the order:
   `flex -> adduct -> rotate` (X -> Z -> Y), which may differ from
   Drake/MuJoCo ordering.
4. **Sign conventions** may differ -- check whether positive angles
   correspond to flexion or extension in each simulator.

## References

- Pinocchio URDF convention: https://gepettoweb.laas.fr/doc/stack-of-tasks/pinocchio/master/doxygen-html/
- Drake MultibodyPlant: https://drake.mit.edu/doxygen_cxx/classdrake_1_1multibody_1_1_multibody_plant.html
- MuJoCo MJCF reference: https://mujoco.readthedocs.io/en/latest/XMLreference.html
