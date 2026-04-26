# A — Project Organization (Weight: 5%)

## Score: 8 / 10

## Evidence

- **Directory layout**: Clean `src/pinocchio_models/` package structure with logical subpackages:
  - `exercises/` — 7 exercise modules (squat, bench_press, deadlift, snatch, clean_and_jerk, gait, sit_to_stand)
  - `addons/` — Gepetto, Pink, Crocoddyl integrations
  - `shared/` — body, barbell, contact, contracts, parity, utils
  - `optimization/` — objectives
- **Configuration**: `pyproject.toml` with hatchling build backend, `Dockerfile` with multi-stage build, `rust_core/` with `Cargo.toml`
- **Governance docs**: `README.md`, `LICENSE`, `CONTRIBUTING.md`, `CODE_OF_CONDUCT.md`, `SECURITY.md`, `CHANGELOG.md`, `SPEC.md`, `AGENTS.md`, `CLAUDE.md`
- **CI**: `.github/workflows/ci-standard.yml`, `.github/dependabot.yml`
- **Tests**: `tests/unit/`, `tests/integration/`, `tests/benchmarks/`, `tests/parity/`
- **Scripts**: `scripts/setup_dev.py`

## Findings

### P0
None.

### P1
None.

### P2
- **No Makefile or task runner** — Common dev tasks require manual command recall. `CONTRIBUTING.md` documents commands but a `Makefile` would reduce friction.
  - File: `CONTRIBUTING.md` (lines 15–19)
- **`docs/` underpopulated** — Only `joint_axis_convention.md` (81 lines) exists. Missing API reference, developer guide, architecture diagrams.
  - File: `docs/joint_axis_convention.md`
- **`examples/` sparse** — Only `generate_all_models.py` and `__init__.py`. Could benefit from per-addon example notebooks or scripts.
  - File: `examples/`
