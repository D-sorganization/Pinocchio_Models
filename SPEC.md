# SPEC.md - Repository Specification Document

<!--
  TEMPLATE VERSION: 1.0.0
  LAST UPDATED: 2026-04-28

  This document is the canonical repository specification for Pinocchio_Models.
  Keep it aligned with the current codebase, entrypoints, and validation rules.
-->

## 1. Identity

| Field | Value |
| --- | --- |
| **Repository Name** | `Pinocchio_Models` |
| **GitHub URL** | `https://github.com/D-sorganization/Pinocchio_Models` |
| **Owner** | D-sorganization |
| **Primary Language(s)** | Python 3.10+ |
| **License** | MIT |
| **Current Version** | 0.1.0 |
| **Spec Version** | 1.0.11 |
| **Last Spec Update** | 2026-04-28 |

## 2. Purpose & Mission

Pinocchio_Models generates Pinocchio-ready URDF models for five classical barbell exercises and a small set of related bodyweight and gait configurations. The repo focuses on deterministic model construction, explicit anthropometric assumptions, and optional integrations for visualization, inverse kinematics, and optimal control.

## 3. Goals & Non-Goals

### Goals

- Generate valid URDF models for squat, bench press, deadlift, snatch, clean and jerk, gait, and sit-to-stand variants.
- Keep shared body and barbell construction logic centralized and reusable.
- Preserve a stable CLI and importable Python API for model generation.
- Support optional addons for Gepetto-viewer, Pink, and Crocoddyl without making them hard runtime dependencies.
- Enforce contract-style validation for geometry, anthropometrics, and URDF output.

### Non-Goals

- Not a general robotics framework beyond the Pinocchio model-generation domain.
- Not a simulation runtime; Pinocchio loads the generated URDF externally.
- Not a hard dependency on optional addon packages.

## 4. Architecture Overview

### System Context

The repository centers on a small Python package, `pinocchio_models`, which exposes reusable model builders and a command-line entrypoint. The code is organized around shared model primitives plus exercise-specific wrappers that assemble full URDF trees.

### Module Map

```text
Pinocchio_Models/
├── src/
│   └── pinocchio_models/
│       ├── __main__.py              # CLI entrypoint (`python3 -m pinocchio_models`)
│       ├── __init__.py              # Public API re-exports
│       ├── addons/                  # Optional integrations
│       │   ├── crocoddyl/
│       │   ├── gepetto/
│       │   └── pink/
│       ├── exercises/               # Exercise-specific builders
│       │   ├── base.py              # Shared builder abstraction
│       │   ├── bench_press/
│       │   ├── clean_and_jerk/
│       │   ├── deadlift/
│       │   ├── gait/
│       │   ├── sit_to_stand/
│       │   ├── snatch/
│       │   └── squat/
│       ├── optimization/            # Exercise objective and trajectory tooling
│       └── shared/                  # Shared body, barbell, contracts, utils, constants
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── parity/
│   └── benchmarks/
├── docs/
├── examples/
├── rust_core/
└── scripts/
```

### Key Components

| Component | Location | Purpose |
| --- | --- | --- |
| CLI entrypoint | `src/pinocchio_models/__main__.py` | Parses exercise selection and generates URDF to stdout or files |
| Public package API | `src/pinocchio_models/__init__.py` | Re-exports the stable builder/spec interfaces |
| Shared exercise base | `src/pinocchio_models/exercises/base.py` | Common URDF build flow, pose hooks, and barbell attachment behavior |
| Shared body model | `src/pinocchio_models/shared/body/body_model.py` | Anthropometric model assembly for the full body |
| Shared barbell model | `src/pinocchio_models/shared/barbell/barbell_model.py` | Olympic barbell construction and plate handling |
| Contracts | `src/pinocchio_models/shared/contracts/` | Input preconditions and output postconditions |
| Geometry and URDF helpers | `src/pinocchio_models/shared/utils/` | Inertia, geometry, XML, and configuration helpers |
| Addons | `src/pinocchio_models/addons/` | Optional Gepetto, Pink, and Crocoddyl integrations |

## 5. Desired Functionality

### Core Features

| # | Feature | Status | Description |
| --- | --- | --- | --- |
| F1 | URDF generation | ✅ | Build valid URDF strings for the supported exercise models |
| F2 | Shared body construction | ✅ | Centralize full-body anthropometrics and link assembly in `shared/body` |
| F3 | Shared barbell construction | ✅ | Build a configurable Olympic barbell in `shared/barbell` |
| F4 | Exercise builders | ✅ | Use `ExerciseModelBuilder` subclasses for per-exercise configuration and initial pose logic |
| F5 | CLI generation | ✅ | Expose `pinocchio-models` and `python3 -m pinocchio_models` for interactive generation |
| F6 | Optional addons | ✅ | Keep Gepetto, Pink, and Crocoddyl integrations import-safe and optional |

### API / Interface Contract

The stable public surface is the importable builder API and the CLI:

- `pinocchio-models <exercise>`
- `pinocchio-models <exercise> --json`
- `python3 -m pinocchio_models <exercise>`
- `python3 -m pinocchio_models <exercise> --json`
- `build_*_model(...)` helpers for each supported exercise
- `ExerciseModelBuilder`, `ExerciseConfig`, `BodyModelSpec`, and `BarbellSpec`
- `create_full_body(...)` and `create_barbell_links(...)`
- Domain exceptions inherit from `PinocchioModelsError` and expose stable
  machine-readable error codes in the `PM000`-style namespace.

Pinocchio-specific runtime behavior is intentionally externalized:

- URDF files are generated here.
- Pinocchio loads the URDF in downstream code.
- Gravity is set programmatically after load, not encoded in the URDF.

### Addon Contract

- `addons/gepetto` provides viewer helpers and must raise a clear `ImportError` when the optional dependency is absent.
- `addons/pink` provides inverse-kinematics helpers and must remain optional.
- `addons/crocoddyl` provides optimal-control helpers and must remain optional.
- Optional addons may be imported only when their dependency is available; core model generation must continue to work without them.

## 6. Data & Configuration

### Input Data

| Input | Format | Source | Notes |
| --- | --- | --- | --- |
| Anthropometric specs | Python dataclasses | `BodyModelSpec`, `BarbellSpec` | Validated at construction time |
| Exercise selections | CLI arguments / Python calls | `__main__.py` and builder functions | Validated before model generation |
| Optional addon dependencies | Python packages | External environment | Treated as optional imports |

### Output Data

| Output | Format | Destination | Notes |
| --- | --- | --- | --- |
| Exercise models | URDF XML strings | stdout or files | Primary package output |
| Visualization/control hooks | Python objects | Optional addon callers | Only when addon dependencies are installed |

### Configuration

- `BodyModelSpec` controls the body mass and height used by the shared body generator.
- `BarbellSpec` controls bar geometry and plate mass.
- The CLI accepts mass, height, plate mass per side, and output directory options.
- `pinocchio_models.shared.constants` centralizes joint limits, grip fractions, and exercise pose defaults.

## 7. Testing Specification

### Testing Strategy

The repo uses pytest for unit, integration, parity, and benchmark coverage. Tests should focus on model validity, addon isolation, contract enforcement, and the CLI/public API.

### Test Organization

| Category | Location | Purpose |
| --- | --- | --- |
| Unit | `tests/unit/` | Validate shared helpers, exercises, addons, and contracts in isolation |
| Integration | `tests/integration/` | Verify end-to-end model construction |
| Parity | `tests/parity/` | Keep model-generation behavior aligned across implementation paths |
| Benchmarks | `tests/benchmarks/` | Track performance regressions in generation workflows |
| Profiling | `scripts/profile_model_generation.py` | Generate scheduled/manual CI profiling reports for representative model-generation paths |
| Examples | `examples/` | Provide runnable core and optional-addon usage scripts for Gepetto, Pink, and Crocoddyl |

### Performance Budget

The model-generation performance budget is defined in
`docs/performance_budget.yml` and explained in `docs/performance_budget.md`.
The budget covers the same representative builders used by
`tests/benchmarks/test_model_generation_benchmark.py` and
`scripts/profile_model_generation.py`. Pull request CI validates that the SLO
artifact remains parseable, complete, and aligned with those benchmark targets;
scheduled or manual profiling runs provide the timing evidence for warning and
breach investigations.

### Coverage Requirements

| Scope | Minimum | Enforced By |
| --- | --- | --- |
| Overall | 80% | CI and pytest-cov |

### Required Test Scenarios

- Shared body and barbell builders emit valid URDF trees.
- Exercise builders build all supported exercise models successfully.
- Optional addon modules fail gracefully when their dependency is missing.
- Example scripts remain present and syntactically valid for each optional addon.
- CLI invocation writes URDF files or stdout as documented.
- Contract helpers reject invalid geometry and mass parameters.

## 8. Quality Standards

### Code Quality Tools

- `ruff check` must pass.
- `ruff format --check` must pass.
- `python3 -m pytest` must pass.
- `mypy` is expected to remain clean for typed public surfaces.

### Design Principles

- DbC: Validate inputs at function boundaries and outputs after generation.
- DRY: Shared body and barbell logic belongs in `shared/`, not duplicated in exercise modules.
- Orthogonality: Exercise modules should use the shared builder surface rather than reaching into low-level geometry internals.
- Law of Demeter: Callers should use `create_full_body()` and `create_barbell_links()` rather than manipulating segment tables directly.

### CI/CD Pipeline

- CI must run the repo-standard lint and test jobs before merge.
- CI may generate line_profiler artifacts on scheduled and manually triggered runs without adding profiling cost to pull request runs.
- Any `pip-audit --ignore-vuln` entry in CI must have matching root-cause,
  dependency, timeline, and removal-criteria metadata in
  `docs/security/pip_audit_ignores.yml`.
- Optional addon tests should mock external dependencies where appropriate.
- Public behavior changes should be reflected in this spec.

## 9. Dependencies

### Runtime Dependencies

- `numpy`
- `matplotlib`

### Optional Dependencies

- `pin` for core Pinocchio integration
- `gepetto-viewer-corba` for visualization
- `pin-pink` for inverse kinematics
- `crocoddyl` for optimal control

### Fleet Dependencies

- No cross-repo runtime dependency is required for core model generation.
- External addon packages are optional and must not block the base package from importing.

## 10. Deployment & Operations

### How to Run

```bash
pip install -e .
pip install -e ".[dev]"
python3 -m pinocchio_models squat
python3 -m pinocchio_models all --output-dir ./models
```

### Build Artifacts

- URDF model files written by the CLI.
- Test reports generated by pytest/coverage in CI.

## 11. Roadmap & Open Issues

### Current Phase

The repository is in active maintenance. Shared model generation is established, and the remaining work is mostly around keeping the optional addon boundaries clean and the shared builder surface consistent.

### Known Limitations

- Optional addons require external packages to be installed.
- Pinocchio-specific loading and gravity setup remain the responsibility of downstream runtime code.

## 12. Change Log

| Date | Version | Changes |
| --- | --- | --- |
| 2026-04-06 | 1.0.0 | Initial repository specification for Pinocchio_Models. |
| 2026-04-11 | 1.0.1 | Decomposed five oversized functions (#128) into single-purpose private helpers; behaviour preserved. |
| 2026-04-11 | 1.0.2 | Split top-2 monolithic addon scripts (#129): `optimal_control.py` and `ik_solver.py` now delegate to focused builder/task/config submodules. Public API and module attributes preserved. |
| 2026-04-27 | 1.0.3 | Optimization: Cached formatting of floats to URDF strings. |
| 2026-04-27 | 1.0.4 | Removed the `numpy<3.0.0` upper bound in `pyproject.toml` dependencies. |
| 2026-04-27 | 1.0.5 | Added `PinocchioModelsError`, `GeometryError`, and `URDFError` exception hierarchy with exports from `__init__.py`. |
| 2026-04-27 | 1.0.6 | Added `--json` CLI flag for structured JSON output. |
| 2026-04-28 | 1.0.7 | Documented the structured domain exception error-code contract. |
| 2026-04-28 | 1.0.8 | Added scheduled/manual CI profiling reports for representative model generation. |
| 2026-04-28 | 1.0.9 | Documented optional-addon example coverage and syntax validation. |
| 2026-04-28 | 1.0.10 | Documented the model-generation performance budget and profiling targets. |
| 2026-04-28 | 1.0.11 | Added auditable pip-audit ignore tracking and CI validation for ignored CVEs. |
