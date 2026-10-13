# API Reference

This reference summarizes the supported public surfaces for generating and
using Pinocchio-compatible exercise models. The package intentionally keeps
runtime dynamics setup outside URDF generation: builders return URDF XML, and
callers decide how to load, configure gravity, visualize, or optimize it.

## Package Entry Points

Import the package-level functions when application code only needs to generate
URDF strings:

```python
from pinocchio_models import build_deadlift_model, build_squat_model

squat_urdf = build_squat_model(
    body_mass=80.0,
    height=1.75,
    plate_mass_per_side=60.0,
)
deadlift_urdf = build_deadlift_model(
    body_mass=85.0,
    height=1.80,
    plate_mass_per_side=80.0,
)
```

Supported builders:

| Function                     | Model                                                 |
| ---------------------------- | ----------------------------------------------------- |
| `build_squat_model`          | Back squat with the barbell fixed to the torso/traps. |
| `build_bench_press_model`    | Supine bench press with hand-attached barbell.        |
| `build_deadlift_model`       | Floor pull with hand-attached barbell.                |
| `build_snatch_model`         | Wide-grip ground-to-overhead lift.                    |
| `build_clean_and_jerk_model` | Two-phase Olympic lift.                               |
| `build_gait_model`           | Bodyweight gait model without barbell links.          |
| `build_sit_to_stand_model`   | Bodyweight sit-to-stand model with its fixture.       |

Each convenience function accepts scalar anthropometry and loading inputs, then
constructs the same immutable specs used by the builder classes:

| Parameter             | Meaning                                        | Constraint            |
| --------------------- | ---------------------------------------------- | --------------------- |
| `body_mass`           | Total body mass in kg.                         | Must be positive.     |
| `height`              | Body height in meters.                         | Must be positive.     |
| `plate_mass_per_side` | Added plate mass on each barbell sleeve in kg. | Must be non-negative. |

Invalid geometry or physics inputs raise package exceptions derived from
`PinocchioModelsError`.

## Configuration Dataclasses

Use spec dataclasses when callers need custom body or barbell dimensions beyond
the scalar convenience functions.

```python
from pinocchio_models import BarbellSpec, BodyModelSpec, ExerciseConfig
from pinocchio_models.exercises.snatch.snatch_model import SnatchModelBuilder

config = ExerciseConfig(
    body_spec=BodyModelSpec(total_mass=72.5, height=1.68),
    barbell_spec=BarbellSpec.womens_olympic(plate_mass_per_side=35.0),
)
urdf = SnatchModelBuilder(config).build()
```

`BodyModelSpec` validates total mass and height. Segment masses, lengths, and
radii are computed from the shared Winter-style segment table in
`pinocchio_models.shared.body.body_anthropometrics`.

`BarbellSpec` validates bar length, shaft length, diameters, unloaded bar mass,
and plate mass. It exposes derived properties for sleeve length, radii, shaft
mass, sleeve mass, and total loaded mass. Use
`BarbellSpec.mens_olympic(...)` or `BarbellSpec.womens_olympic(...)` for
standard bars.

## Builder Classes

Builder classes are useful when extending or testing exercise-specific
behavior:

```python
from pinocchio_models.exercises.deadlift.deadlift_model import DeadliftModelBuilder

builder = DeadliftModelBuilder()
urdf = builder.build()
```

`ExerciseModelBuilder` defines the common pipeline:

1. Create the root `<robot>` element.
2. Add the full body with `create_full_body`.
3. Add barbell links when `uses_barbell` is true.
4. Attach the barbell or fixture through `attach_barbell`.
5. Stamp exercise defaults through `set_initial_pose`.
6. Validate the URDF tree before serialization.

Subclasses implement `exercise_name`, `attach_barbell` and `set_initial_pose`
and may override `uses_barbell`. The barbell lifts subclass `SpecLiftBuilder`
(`exercises/spec_lift.py`), which implements both hooks from the spec `start`
via-pose; they define `spec_exercise` (and the squat and bench press override
`attach_barbell` for the torso weld and the bench support).

## Loading URDF in Pinocchio

Generated URDF does not include gravity or a floating-base joint. Configure both
in Pinocchio at runtime:

```python
import pinocchio as pin
from pinocchio_models import build_squat_model

urdf = build_squat_model(body_mass=80.0, height=1.75, plate_mass_per_side=60.0)
model = pin.buildModelFromXML(urdf, pin.JointModelFreeFlyer())
model.gravity = pin.Motion.Zero()
model.gravity.linear[2] = -9.80665
```

The project uses Z-up, X-forward coordinates. See
[joint_axis_convention.md](joint_axis_convention.md) before porting joint
states to simulators with different body-frame conventions.

## Forward Kinematics

`pinocchio_models.forward_kinematics(exercise, q)` computes frame and segment
poses for an exercise model using `pinocchio.forwardKinematics` and
`pinocchio.updateFramePlacements`:

```python
import pinocchio as pin
from pinocchio_models import forward_kinematics
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

model = load_model(build_urdf("squat"))
q = pin.neutral(model)
poses = forward_kinematics("squat", q)  # or forward_kinematics(model, q)
pelvis_pose = poses["pelvis"]
```

`exercise` is a manifest exercise id or a ready `pinocchio.Model`. `q` must have
shape `(model.nq,)` and contain only finite values; violations raise `ValueError`
(or `TypeError` if `exercise` is invalid). Returns a dictionary mapping every
frame and segment name to its `pinocchio.SE3` pose in the world coordinate frame.

## Inverse Dynamics (RNEA)

`pinocchio_models.inverse_dynamics(exercise, q, v, a)` wraps `pinocchio.rnea`
on the free-flyer exercise model (standard gravity) and returns the generalized
forces `tau`:

```python
import numpy as np
import pinocchio as pin
from pinocchio_models import inverse_dynamics
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

model = load_model(build_urdf("squat"))
q, v, a = pin.neutral(model), np.zeros(model.nv), np.zeros(model.nv)
tau = inverse_dynamics("squat", q, v, a)  # or inverse_dynamics(model, q, v, a)
```

`exercise` is a manifest exercise id or a ready `pinocchio.Model`. `q` must have
shape `(model.nq,)`, `v` and `a` shape `(model.nv,)`, all finite; violations
raise `ValueError`. In a static pose (`v = a = 0`) the root vertical force
`tau[2]` equals total mass times gravity.

## Ground Reaction Forces and Centre of Pressure

`pinocchio_models.ground_reaction_forces(exercise, q)` solves constrained
contact dynamics for the foot-ground contacts of
`shared.contact.contact_model.foot_contact_points()` (four sole corners per
foot) and returns per-foot and total ground reaction forces plus the centre of
pressure (CoP):

```python
import pinocchio as pin
from pinocchio_models import ground_configuration, ground_reaction_forces
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

model = load_model(build_urdf("gait"))
q = ground_configuration(model, pin.neutral(model))  # soles on the floor
grf = ground_reaction_forces("gait", q)
grf.total_force          # (3,) N, ground on body, world axes; [2] ~= m * g
grf.per_foot["foot_l"]   # FootGRF(force, moment, cop, in_contact)
grf.cop                  # (3,) on the floor plane, or None
grf.support_polygon      # (k, 2) convex hull of the active contact points
```

Formulation: quasi-static standing. Every non-root joint is locked at `q`
(`pinocchio.buildReducedModel`, joints held by ideal servos); contact points
within `contact_tolerance_m` (default 1 mm) of the floor `z = 0` become rigid
bilateral `CONTACT_3D` constraints, and `pinocchio.constraintDynamics` solves
at `v = 0`, `tau = 0` with proximal regularisation, which picks the
minimum-norm force split among the redundant corner contacts. With three or
more non-collinear active points the total vertical force equals `m * g`.

No contact is explicit: a foot with no active point has zero force and moment
and `cop=None`; with no active point at all, the total force and moment are
zero and `grf.cop is None`. A welded root (`bench_press`) raises `ValueError`.

## Recording a Rollout (Headless)

`pinocchio_models.record_rollout(exercise, rollout, output_path, *, fps=30)`
replays a configuration trajectory with
`pinocchio.visualize.MeshcatVisualizer` and writes a **self-contained static
HTML file**: the model's visual geometry plus a keyframed Meshcat animation
with one keyframe per configuration. Opening the file in any browser plays the
rollout; no server is needed afterwards. Requires the optional extra:

```bash
pip install -e ".[meshcat]"
```

```python
import numpy as np
import pinocchio as pin
from pinocchio_models import record_rollout
from pinocchio_models.recording import recorded_frame_count
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

model = load_model(build_urdf("squat"))
start = pin.neutral(model)
end = start.copy()
end[7:] = 0.5 * (model.lowerPositionLimit[7:] + model.upperPositionLimit[7:])
frames = [pin.interpolate(model, start, end, t) for t in np.linspace(0, 1, 60)]

rec = record_rollout("squat", frames, "squat_rollout.html", fps=30)
rec.frame_count, rec.duration_s, rec.size_bytes   # 60, 2.0, ~1 MB
recorded_frame_count(rec.path)                    # 60, decoded from the file
```

`rollout` is either a sequence of configurations (a kinematic replay, e.g.
interpolated exercise keyframes) or a callable that receives the resolved
`pinocchio.Model` and returns the configurations, so a forward-dynamics
simulation can feed the recorder directly. Every configuration must have shape
`(model.nq,)` and be finite; the rollout must be non-empty, `fps` a positive
whole number and `output_path` an `.html` file in an existing directory.
Violations raise `ValueError` before any server starts.

Headless guarantees: a private Meshcat server is started on `127.0.0.1` only
for the duration of the call and is always shut down before returning (also on
error); no browser or GUI window is opened. As a postcondition the written
file is non-empty and decodes to exactly one keyframe per configuration.

Limitation: the artifact is an HTML animation, not an encoded video (MP4 or
WebM); producing pixels needs a browser or an offscreen renderer, so the
`video_export` capability is `partial`.
The GRF/CoP math is engine-independent and lives in
`pinocchio_models.shared.contact.grf`.

## Forward Dynamics with Ground Contact (aba)

`pinocchio_models.simulate_forward_dynamics(exercise, q0, duration=...)`
integrates `pinocchio.aba` with compliant ground contact;
`contact_forward_dynamics(exercise, q, v, tau)` evaluates one step:

```python
import pinocchio as pin
from pinocchio_models import (
    ground_configuration,
    holding_servo,
    simulate_forward_dynamics,
)
from pinocchio_models.shared.parity.fingerprint import build_urdf, load_model

model = load_model(build_urdf("squat"))
q0 = ground_configuration(model, pin.neutral(model))  # soles on the floor
rollout = simulate_forward_dynamics(
    model, q0, duration=0.5, servo=holding_servo(model, q0)
)
rollout.q, rollout.v           # (n + 1, nq), (n + 1, nv)
rollout.ground_force[-1]       # (3,) N; [2] ~= m * g once settled
rollout.min_contact_height     # (n + 1,) m; negative = sole penetration
rollout.final_grf              # GroundReactionForces (per foot, CoP)
```

Contact model: the foot sole corners of `foot_contact_points()` touch a flat
floor at `z = 0` through a unilateral spring-damper (the floor never pulls)
with viscous friction clipped to the Coulomb cone `mu F_n`
(`shared.contact.penalty`). The forces enter `aba` as external spatial forces
on the supporting joints. Gains derive from the model weight `W` and a static
sole penetration `delta` (default 2 mm): `k = W / (n delta)` per point and
critical damping of the supported-body mode `sqrt(g / delta)`. A penalty law
was chosen over a rigid `constraintDynamics` solve per step because it is
defined in every state, releases contacts that lift off and bounds friction.

Integration: semi-implicit Euler on the configuration manifold with the
contact and servo damping taken linearly implicit,
`v+ = v + dt (M + dt C)^-1 M ddq`. The default `dt` is the undamped
linearised stability limit at `q0` (all contacts closed) divided by
`TIME_STEP_SAFETY_FACTOR = 2`; an explicit `dt` above that is rejected.

The root is unactuated. `holding_servo(exercise, q)` returns a `JointServo`
(PD per joint at bandwidth 20 rad/s from the `crba` diagonal, plus the static
holding torques `g(q) - J^T w` of the rigid ground reaction
`ground_reaction_forces`); pass `servo=None` for passive joints and
`ground_contact=False` for free fall. Limits: only the sole corners contact
the floor (no other body-environment or self collision), friction has no
static stick, and the step is fixed, so the capability is rated `partial`.

## Initial Pose Metadata

Exercise builders write `initial_position` attributes onto URDF joints to record
intended start poses; the barbell lifts also record the pelvis start placement
as `initial_root_xyz` / `initial_root_rpy` on `<robot>` (the spec `start`
via-pose, LIFT-3). Pinocchio ignores unknown URDF attributes, so callers must
apply those values explicitly (`get_initial_configuration` seeds the
free-flyer from the root placement):

```python
import pinocchio as pin
from pinocchio_models.exercises.deadlift.deadlift_model import build_deadlift_model
from pinocchio_models.shared.utils.urdf_helpers import get_initial_configuration

urdf = build_deadlift_model(body_mass=85.0, height=1.80, plate_mass_per_side=80.0)
model = pin.buildModelFromXML(urdf, pin.JointModelFreeFlyer())
q0 = get_initial_configuration(model, urdf)
```

`get_initial_configuration` starts from `pin.neutral(model)` and overlays scalar
joint defaults where matching joints exist.

## Optimization Objective Helpers

The optimization package provides lightweight phase descriptions and linear
interpolation helpers:

```python
from pinocchio_models.optimization.exercise_objectives import (
    get_exercise_objective,
)
from pinocchio_models.optimization.trajectory_optimizer import interpolate_phases

objective = get_exercise_objective("deadlift")
trajectory = interpolate_phases(objective, n_frames=50)
```

Objective data is split by exercise under `pinocchio_models.optimization.objectives`.
`pinocchio_models.optimization.exercise_objectives` remains as a compatibility
re-export module.

## CLI

The installed script and module entry point share the same interface:

```bash
pinocchio-models squat --mass 80 --height 1.75 --plates 60 --output-dir models
python3 -m pinocchio_models all --json
```

Use `--output-dir` to write URDF files. Without it, XML is emitted to stdout.
Use `--json` for structured output containing the exercise name, URDF text,
parameters, output path, and success flag.
