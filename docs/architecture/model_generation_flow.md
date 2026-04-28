# Model Generation Architecture

Issue: [#194](https://github.com/D-sorganization/Pinocchio_Models/issues/194).

This page diagrams the code path that turns CLI or Python API inputs into
Pinocchio-ready URDF XML. It is intentionally scoped to the core package
boundary: generated URDF is this repository's output, while Pinocchio model
loading, floating-base insertion, and gravity setup happen in downstream code.

## Component Diagram

```mermaid
flowchart LR
    CLI["CLI<br/>src/pinocchio_models/__main__.py"]
    API["Python API<br/>build_*_model(...)"]
    Builder["ExerciseModelBuilder<br/>exercises/base.py"]
    Exercise["Exercise modules<br/>squat, bench_press, deadlift,<br/>snatch, clean_and_jerk,<br/>gait, sit_to_stand"]
    Body["Shared body builder<br/>shared/body/body_model.py"]
    Barbell["Shared barbell builder<br/>shared/barbell/barbell_model.py"]
    Contracts["Contracts<br/>shared/contracts"]
    Helpers["URDF helpers<br/>shared/utils/urdf_helpers.py"]
    URDF["URDF XML string or .urdf file"]
    Pin["Downstream Pinocchio runtime<br/>buildModelFromXML + FreeFlyer + gravity"]
    Addons["Optional addons<br/>Gepetto, Pink, Crocoddyl"]

    CLI --> Builder
    API --> Builder
    Builder --> Exercise
    Builder --> Body
    Builder --> Barbell
    Body --> Helpers
    Barbell --> Helpers
    Exercise --> Helpers
    Helpers --> Contracts
    Contracts --> URDF
    URDF --> Pin
    Pin --> Addons
```

### Boundaries

| Boundary          | Owned here                                                                   | Owned by downstream caller                                 |
| ----------------- | ---------------------------------------------------------------------------- | ---------------------------------------------------------- |
| Model description | URDF links, joints, inertias, visuals, collisions, and initial-pose metadata | Pinocchio model/data objects                               |
| Floating base     | Documented expectation only                                                  | `pin.JointModelFreeFlyer()` during load                    |
| Gravity           | Not encoded in URDF                                                          | `model.gravity` assignment                                 |
| Optional tooling  | Import-safe addon wrappers                                                   | Installed Gepetto, Pink, Crocoddyl, and Pinocchio packages |

## Generation Sequence

```mermaid
sequenceDiagram
    participant User
    participant CLI as CLI / Python API
    participant Builder as ExerciseModelBuilder
    participant Body as create_full_body
    participant Barbell as create_barbell_links
    participant Exercise as Exercise hook
    participant Contracts as URDF postconditions
    participant Output as URDF output
    participant Pin as Downstream Pinocchio

    User->>CLI: choose exercise, mass, height, plates
    CLI->>Builder: build exercise URDF
    Builder->>Body: append pelvis-root full body links and joints
    alt barbell exercise
        Builder->>Barbell: append shaft, sleeves, and fixed welds
    else bodyweight or fixture exercise
        Builder-->>Builder: skip barbell link creation
    end
    Builder->>Exercise: attach barbell or fixture
    Exercise->>Exercise: stamp initial_position metadata
    Builder->>Contracts: ensure valid URDF tree
    Contracts-->>Builder: validated XML tree
    Builder->>Output: serialize XML to stdout, JSON, or files
    Output->>Pin: caller loads XML with FreeFlyer
    Pin->>Pin: caller sets gravity and applies optional initial pose
```

## Key Design Rules

- URDF is the interchange format for all generated models.
- Z is vertical, X is forward, and Y completes the right-hand frame.
- The pelvis is the URDF root link; Pinocchio adds the floating base at load
  time.
- Compound anatomical joints are represented as chains of single-axis URDF
  revolute joints connected by virtual links.
- Exercise modules use `create_full_body()` and `create_barbell_links()`
  instead of duplicating segment or barbell internals.
- `initial_position` attributes are metadata. Pinocchio ignores them unless a
  caller explicitly applies them with `get_initial_configuration(...)`.

## Extension Checklist

When adding or changing an exercise builder:

1. Add shared dimensions or limits to `shared/constants.py` or the relevant
   spec dataclass instead of duplicating values in the exercise module.
2. Reuse `ExerciseModelBuilder.build()` unless the whole assembly flow changes.
3. Keep barbell attachment logic in the exercise hook and leave body/barbell
   construction in the shared builders.
4. Validate generated XML through the existing postcondition helpers.
5. Update this page if the data flow, runtime boundary, or optional-addon
   boundary changes.
