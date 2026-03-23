# AGENTS.md -- Pinocchio_Models

## Safety

- Never bypass CI checks or use `--admin` flag on `gh pr merge`.
- All PRs must pass CI before merging -- no exceptions.
- Never force-push to `main`.

## Python Standards

- Use `python3`, never `python`.
- Target Python 3.10+ (`from __future__ import annotations`).
- Format with `ruff format`, lint with `ruff check`.
- Type hints on all public function signatures.

## Architecture

- **URDF format** for all models (standard for Pinocchio).
- **Z-up convention**: vertical is Z, forward is X.
- **Pinocchio loads URDF** and adds floating base via `pin.JointModelFreeFlyer()`.
- **Gravity is NOT in URDF** -- set programmatically via `model.gravity`.
- Pinocchio API: NO `computeTotalEnergy`; use `computeKineticEnergy` + `computePotentialEnergy` separately.

## Design Principles

### Design by Contract (DbC)

- Preconditions: validate all inputs at function entry (`require_*` guards).
- Postconditions: validate outputs after computation (`ensure_*` guards).
- Never silently accept invalid geometry or physics parameters.

### Test-Driven Development (TDD)

- Write tests before implementation.
- Every public function has at least one test.
- Tests for addons mock external dependencies (pinocchio, gepetto, pink, crocoddyl).

### DRY (Don't Repeat Yourself)

- Inertia formulas in `geometry.py`, URDF generation in `urdf_helpers.py`.
- Body proportions in `_SEGMENT_TABLE`, never duplicated.
- Exercise builders share `ExerciseModelBuilder` base class.

### Law of Demeter

- Exercise modules call `create_full_body()` / `create_barbell_links()`.
- They never manipulate internal segment tables or inertia details.

## Addon Integration

- **Gepetto-viewer**: visualization via `gepetto-viewer-corba`.
- **Pink**: task-based inverse kinematics for pose targeting.
- **Crocoddyl**: optimal control for motion optimization.
- All addons use try/except imports and raise clear `ImportError` when needed.
- Addons are usable WITHOUT their packages installed.

## CI/CD

- `ruff check` AND `ruff format --check` must both pass.
- No TODO/FIXME in source files unless tracked by a GitHub issue.
- Tests run with `python3 -m pytest` (never bare `pytest`).
- Coverage threshold: 80%.
