# Deep Object Traversal Audit

Issue: [#161](https://github.com/D-sorganization/Pinocchio_Models/issues/161).
Fleet triage wave 33. Sibling audits: Gas #2588, Tools_Private #263, MEB #63,
Worksheet-Workshop #173.

## Goal

Identify deep attribute-chain accesses (`a.b.c.d` or longer) in the Python
package under `src/pinocchio_models/` and classify each as either a
framework/idiom artefact (benign) or a genuine Law-of-Demeter (LoD) violation
that couples a caller to transitive structure.

## Methodology

1. Grep `src/` for attribute chains of length >= 3 (three or more dots between
   identifiers).
2. Strip import statements, dotted docstring cross-references, and fully
   qualified type annotations — these are name-resolution, not runtime
   traversal.
3. Classify the remaining runtime call sites.

Search used:

```
grep -rnE '\.[a-zA-Z_]+\.[a-zA-Z_]+\.[a-zA-Z_]+' src/ --include='*.py'
  | grep -vE '(^\s*from |^\s*import |pinocchio_models\.|``)'
```

## Findings

The audit surfaced **only two** non-import deep-traversal sites in the
entire `src/` tree, and both are three-level (not four-plus). No Qt or GUI
framework idioms are present — this is a pure modelling/simulation package.

| # | File | Line | Expression | Classification |
| - | ---- | ---- | ---------- | -------------- |
| 1 | `src/pinocchio_models/exercises/base.py` | 142 | `self.config.barbell_spec.shaft_length` | Benign — canonical config dataclass traversal |
| 2 | `src/pinocchio_models/exercises/squat/squat_model.py` | 57 | `self.config.body_spec.height` | Benign — canonical config dataclass traversal |

### Why both are benign

Both sites read a single leaf scalar from a nested `@dataclass` config tree
that is the documented public interface of `ExerciseConfig`. The parent
`self.config` is a value object whose sub-specs (`barbell_spec`, `body_spec`,
`contact_spec`, …) are themselves immutable dataclasses. This is the
"Configuration Object" pattern — reaching through it to read a published
field is not the kind of structural coupling LoD targets, because the
intermediate dataclasses expose no behaviour and have no invariants that
could be broken by the reach-through.

Introducing `@property` wrappers such as `config.shaft_length` would duplicate
every sub-spec field onto the parent type and double the surface area of the
config contract without eliminating any real coupling. The existing shape
is preferred.

### Framework idioms (not found)

Sibling repos (notably Worksheet-Workshop and MEB) flagged long Qt chains
such as `self.window.centralWidget().layout().addWidget(...)` as Qt-idiom
benign. `pinocchio_models` uses no Qt, PySide, or Tk, so no such chains
exist here. Pinocchio / Pink / Gepetto-viewer bindings are used as flat
function calls in the addons package, not via deep member traversal.

### LoD violations (not found)

No call site was found where a caller reaches through a behaviour-bearing
object (e.g. a model, solver, or builder) into its internal collaborators.
The `shared/` layer deliberately exposes top-level helpers
(`set_joint_default`, `get_initial_configuration`, geometry utilities) that
callers invoke directly rather than by traversing into a model object.

## Recommendations

- **No refactor required.** The two traversal sites are healthy dataclass
  reads.
- **Keep this low-coupling property.** When adding new exercises or addons,
  continue to pass leaf scalars into helpers rather than handing around
  `self.config` and letting callees reach in.
- **Revisit if Qt viewer integration lands.** Any future GUI layer should be
  audited separately because Qt's widget tree naturally produces long
  chains that are idiomatic rather than problematic.

## Closes

Resolves #161.
