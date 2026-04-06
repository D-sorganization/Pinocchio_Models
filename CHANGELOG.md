# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-03-31

### Documented (cross-repo duplication — issue #104)

- **DRY**: Added header comment to `preconditions.py` documenting that the six
  core `require_*` functions are intentionally duplicated across
  Pinocchio_Models, MuJoCo_Models, and OpenSim_Models, and pointing to issue
  #104 for migration options if a shared package is ever warranted.

### Fixed (A-N Assessment Remediation — issue #100)

- **DbC**: Added input validation to `main()` in `__main__.py` for `--mass`, `--height`, `--plates` CLI arguments.
- **DbC**: Added precondition guards (`n_frames >= 2`, non-empty phases) to `interpolate_phases()` in `trajectory_optimizer.py`.
- **LoD**: Broke `Path(__file__).resolve().parent.parent` chain in `setup_dev.py` into named `_SCRIPT_DIR` and `PROJECT_ROOT` intermediates.
- **LoD**: Extracted `sys.stdout` into a local variable in `__main__.py` to avoid repeated chained attribute access.
- **Documentation**: Added missing docstrings to `main()` in `setup_dev.py`, `ExerciseModelBuilder.__init__()`, `BarbellSpec.__post_init__()`, and `BodyModelSpec.__post_init__()`.
- **Documentation**: Added docstrings to `shaft_radius` and `sleeve_radius` properties in `BarbellSpec`.

## [0.1.0] - 2026-03-22

### Added
- Five exercise model builders: squat, bench press, deadlift, snatch, clean and jerk.
- Full-body model with Winter (2009) anthropometric proportions.
- Olympic barbell model (men's and women's).
- Design-by-Contract precondition and postcondition guards.
- Optional addon integrations: Gepetto-viewer, Pink IK, Crocoddyl OC.
- CLI entry point: `python3 -m pinocchio_models`.
- Hypothesis property-based tests for geometry functions.
- Comprehensive test suite with >80% coverage.
- CI pipeline with Python 3.10, 3.11, 3.12 matrix.
- Governance docs: CONTRIBUTING.md, SECURITY.md, CODE_OF_CONDUCT.md.

### Fixed
- Barbell now attached to both hands in all grip exercises (was left-hand only).
- `extract_joint_torques` no longer re-solves the OCP.
- Postcondition checks raise `ValueError` (not `AssertionError`).

### Changed
- Removed unused `scipy` and `lxml` core dependencies.
- Factored duplicate `attach_barbell` logic into base class.
- Extracted magic numbers for joint limits into named constants.
- Tightened mypy: `disallow_untyped_defs = true`.
- Made `bandit` and `pip-audit` hard CI failures.
