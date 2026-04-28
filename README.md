# Pinocchio_Models

Pinocchio-based multibody dynamics simulation for five classical barbell exercises, with optional integration for Gepetto-viewer visualization, Pink inverse kinematics, and Crocoddyl optimal control.

## Exercises

| Exercise       | Description                                            |
| -------------- | ------------------------------------------------------ |
| Back Squat     | Barbell on upper trapezius, hip/knee flexion-extension |
| Bench Press    | Supine pressing, barbell in hands                      |
| Deadlift       | Hip-hinge pull from ground, barbell in hands           |
| Snatch         | Ground-to-overhead in one motion, wide grip            |
| Clean and Jerk | Two-phase Olympic lift, shoulder-width grip            |

## Architecture

- **URDF format** for all models (standard Pinocchio input)
- **Z-up convention** (vertical is Z, forward is X)
- **Winter (2009)** anthropometric proportions for body segments
- **IWF/IPF** regulation barbell dimensions
- Pinocchio adds floating base programmatically via `pin.JointModelFreeFlyer()`

## Installation

```bash
# Core (URDF generation only -- no external physics deps)
pip install -e .

# With development tools
pip install -e ".[dev]"

# With Pinocchio ecosystem
pip install -e ".[all-addons]"
```

## Optional Addons

### Gepetto-viewer (Visualization)

```bash
pip install -e ".[gepetto]"
```

```python
from pinocchio_models.addons.gepetto.viewer import create_viewer, display_configuration
```

### Pink (Inverse Kinematics)

```bash
pip install -e ".[pink]"
```

```python
from pinocchio_models.addons.pink.ik_solver import create_ik_problem, solve_pose
```

### Crocoddyl (Optimal Control)

```bash
pip install -e ".[crocoddyl]"
```

```python
from pinocchio_models.addons.crocoddyl.optimal_control import create_exercise_ocp, solve_trajectory
```

## Quick Start

```python
from pinocchio_models.exercises.squat.squat_model import build_squat_model

# Generate URDF for an 80 kg person with 140 kg total barbell
urdf_str = build_squat_model(body_mass=80.0, height=1.75, plate_mass_per_side=60.0)

# Load into Pinocchio
import pinocchio as pin
model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
model.gravity = pin.Motion.Zero()
model.gravity.linear[2] = -9.80665  # Z-up
```

## Applying Initial Poses

The URDF builder writes `initial_position` attributes onto joint elements to
record the intended starting configuration for each exercise (e.g. the
hip-flexed starting position for a deadlift).

> **Important:** Pinocchio does *not* read `initial_position` attributes when
> loading a URDF.  The attributes are metadata only — they have no effect on
> simulation unless consumed explicitly.

Use `get_initial_configuration` to convert those attributes into a numpy
configuration vector suitable for `pin.forwardKinematics` and friends:

```python
import pinocchio as pin
from pinocchio_models.exercises.deadlift.deadlift_model import build_deadlift_model
from pinocchio_models.shared.utils.urdf_helpers import get_initial_configuration

# Build the URDF
urdf_str = build_deadlift_model(body_mass=85.0, height=1.80, plate_mass_per_side=80.0)

# Load into Pinocchio
model = pin.buildModelFromXML(urdf_str, pin.JointModelFreeFlyer())
data = model.createData()

# Obtain a configuration vector with the exercise starting pose applied
q0 = get_initial_configuration(model, urdf_str)

# Use it for forward kinematics, IK seeding, visualisation, etc.
pin.forwardKinematics(model, data, q0)
pin.updateFramePlacements(model, data)
```

Without `get_initial_configuration`, `pin.neutral(model)` returns an
all-zeros (identity) pose, which ignores the documented starting angles.

## Examples

The `examples/` directory contains runnable scripts for core model generation
and each optional addon:

```bash
python examples/generate_all_models.py
python examples/basic_usage.py
python examples/gepetto_visualization.py
python examples/pink_inverse_kinematics.py
python examples/crocoddyl_optimal_control.py
```

Install the matching optional extra before running an addon example, such as
`pip install -e ".[pink]"` for Pink or `pip install -e ".[crocoddyl]"` for
Crocoddyl.

## Testing

```bash
pip install -e ".[dev]"
python3 -m pytest tests/ -v --tb=short
```

## Docker

```bash
docker build --target runtime -t pinocchio-models .
docker run -it pinocchio-models python3 -m pytest tests/ -v
```

## License

MIT License. See [LICENSE](LICENSE).
