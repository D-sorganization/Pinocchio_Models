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

| Function | Model |
| --- | --- |
| `build_squat_model` | Back squat with the barbell fixed to the torso/traps. |
| `build_bench_press_model` | Supine bench press with hand-attached barbell. |
| `build_deadlift_model` | Floor pull with hand-attached barbell. |
| `build_snatch_model` | Wide-grip ground-to-overhead lift. |
| `build_clean_and_jerk_model` | Two-phase Olympic lift. |
| `build_gait_model` | Bodyweight gait model without barbell links. |
| `build_sit_to_stand_model` | Bodyweight sit-to-stand model with its fixture. |

Each convenience function accepts scalar anthropometry and loading inputs, then
constructs the same immutable specs used by the builder classes:

| Parameter | Meaning | Constraint |
| --- | --- | --- |
| `body_mass` | Total body mass in kg. | Must be positive. |
| `height` | Body height in meters. | Must be positive. |
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

Subclasses usually override only `exercise_name`, `grip_offset_fraction`,
`uses_barbell`, `attach_barbell`, and `set_initial_pose`.

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

## Initial Pose Metadata

Exercise builders write `initial_position` attributes onto URDF joints to record
intended start poses. Pinocchio ignores unknown URDF attributes, so callers must
apply those values explicitly:

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
