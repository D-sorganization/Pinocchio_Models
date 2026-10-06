# Joint Axis Convention

## Canonical Frame

Pinocchio Models follows the fleet parity standard (issue #435):

- **Z up**, **X forward**, **Y left**.
- Left bilateral segments sit at **+Y**, right segments at **-Y**.
- Every joint frame is aligned with the world at q=0 (no rotated joint origins),
  so the `<axis>` literal of a coordinate equals its canonical axis.

Axes and joint origins are read from the vendored standard
(`_canonical/biomech_parity_standard.json`, `kinematics.axes` and
`kinematics.joints`) by `shared/body/canonical_topology.py`; they are never
written as literals. Right-side axes are listed; `mirror` negates them on the
left.

| Coordinate | Right axis | Mirrored on left | Positive direction |
|------------|-----------|------------------|--------------------|
| Hip, shoulder, elbow, wrist, knee, ankle flexion | `(0,-1,0)` | no | distal segment swings forward |
| Hip, shoulder adduction; wrist deviation; ankle inversion | `(1,0,0)` | yes | toward the midline |
| Hip, shoulder rotation | `(0,0,1)` | yes | internal rotation |
| Lumbar flexion, neck flexion | `(0,1,0)` | no | bends forward |
| Lumbar lateral bend | `(-1,0,0)` | no | bends toward the left |
| Lumbar rotation | `(0,0,1)` | no | chest turns toward the left |

Sign consequences: knee flexion is negative, positive ankle flexion is
dorsiflexion, a documented external rotation is a negative hip or shoulder
rotation, and a negative shoulder adduction is abduction.

## Multi-DOF Joints

Compound joints chain revolute joints through virtual links in the order
`flex -> adduct -> rotate` (hip, shoulder), `flex -> deviate` (wrist),
`flex -> invert` (ankle) and `flex -> lateral -> rotate` (lumbar). Axes are
canonical at the all-zero pose; the parity probe rotates one coordinate at a
time from there, so the chain order does not affect the check.

## Supine Bench Press

The bench press URDF has a `bench` root link and a fixed joint `pelvis_to_bench`
pitched -90 degrees about Y, so body +X (chest) points to world +Z. Shoulder
flexion of +90 degrees then raises the arms straight up.

## Verification

`python -m pinocchio_models.shared.parity.fingerprint --all --out DIR` loads
each exercise in Pinocchio and reports measured axes, the pelvis rotation and
segment origins at the standard test poses; `tests/parity/` requires zero
`axis.*`, `side.*`, `origin.*` and `pose.*` divergences.

## Porting Between Simulators

Drake, MuJoCo and OpenSim packs use the same standard, so a joint angle has
the same physical meaning in every pack. OpenSim is Y-up; its frame is rotated
into the canonical frame by the standard's `to_canonical` matrix.
