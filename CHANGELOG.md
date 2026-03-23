# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
