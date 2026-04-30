# CLAUDE.md -- Pinocchio_Models

## Branch Policy

All work on `main` branch. PRs target `main`.

## What This Is

Pinocchio-based multibody dynamics simulation for classical barbell exercises
(squat, deadlift, bench press, snatch, clean & jerk) plus gait and
sit-to-stand. Python package that generates URDF XML strings, loadable by
Pinocchio with a free-flyer floating base.

## Key Directories

- `src/pinocchio_models/` -- importable package (source of truth)
- `src/pinocchio_models/exercises/` -- one sub-package per exercise (squat, deadlift, bench_press, snatch, clean_and_jerk, gait, sit_to_stand)
- `src/pinocchio_models/exercises/base.py` -- `ExerciseModelBuilder` base class
- `src/pinocchio_models/optimization/` -- trajectory optimiser, exercise objectives
- `src/pinocchio_models/shared/` -- barbell, body model, contracts, constants, contact, geometry, URDF helpers
- `src/pinocchio_models/addons/` -- optional integrations (gepetto, pink, crocoddyl)
- `tests/` -- pytest suite (unit/, integration/, parity/, benchmarks/)
- `rust_core/` -- optional Rust accelerator (PyO3)
- `.github/workflows/ci-standard.yml` -- CI pipeline

## Python and Tooling

- **Python >=3.10**. Always use `python3`, never `python`.
- **Formatter:** ruff format (line-length 88).
- **Linter:** ruff check.
- **Type checker:** mypy (strict on src/).
- **Build backend:** hatchling.

## Development Commands

```bash
pip install -e ".[dev]"                         # install with dev deps
ruff check src scripts tests examples           # lint
ruff format src scripts tests examples          # format
ruff format --check src scripts tests examples  # format check (CI mode)
mypy src --config-file pyproject.toml           # type check
python3 -m pytest -m "not slow and not requires_pinocchio" --cov=src --cov-fail-under=80
```

## CI Requirements (All Must Pass)

1. `ruff check` -- zero violations
2. `ruff format --check` -- zero diffs
3. `mypy` -- no errors on src/
4. No TODO/FIXME without tracked GitHub issue
5. `bandit` security scan -- no high-severity findings
6. `pip-audit` -- no known vulnerabilities
7. pytest with **80% coverage minimum**
8. Multi-version matrix: Python 3.10, 3.11, 3.12

## Coding Standards

- **No bare except** -- catch specific exceptions
- **No wildcard imports**
- **Type hints** on all public functions
- **Docstrings** on all public functions and classes
- **DbC:** preconditions validate inputs with `require_*` guards (`ValueError`), postconditions verify outputs with `ensure_*` guards
- **DRY:** shared base class (`ExerciseModelBuilder`), shared barbell/body models, shared URDF helpers
- **Law of Demeter:** exercise modules call `create_full_body()` / `create_barbell_links()`, never manipulate internal segment tables or inertia details

## Architecture Notes

- All exercises inherit from `ExerciseModelBuilder` (base.py)
- Barbell attachment and initial pose are exercise-specific
- **URDF format** for all models (standard Pinocchio input)
- **Z-up convention**: vertical is Z, forward is X
- **Winter (2009)** anthropometric proportions for body segments
- **IWF/IPF** regulation barbell dimensions
- Pinocchio adds floating base via `pin.JointModelFreeFlyer()`
- **Gravity is NOT in URDF** -- set programmatically via `model.gravity`
- Pinocchio API: NO `computeTotalEnergy`; use `computeKineticEnergy` + `computePotentialEnergy` separately

## Addon Integration

- **Gepetto-viewer** (`.[gepetto]`): visualization via `gepetto-viewer-corba`
- **Pink** (`.[pink]`): task-based inverse kinematics for pose targeting
- **Crocoddyl** (`.[crocoddyl]`): optimal control for motion optimization
- All addons use try/except imports and raise clear `ImportError` when missing
- Addons are testable WITHOUT their packages installed (mocked in tests)

## Docker

Multi-stage Dockerfile (builder / runtime / training):
- Base: `continuumio/miniconda3` with Pinocchio ecosystem via conda-forge
- Training stage adds `gymnasium` and `stable-baselines3`

## Git Workflow

- Conventional Commits: `feat:`, `fix:`, `docs:`, `test:`, `refactor:`, `chore:`
- Branch naming: `feat/description`, `fix/description`, `docs/description`
- PRs must pass CI before merge
- Never force-push to `main`
- Never use `--admin` to bypass branch protection
