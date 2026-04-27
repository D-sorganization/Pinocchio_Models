# L — Maintainability (Weight: 8%)

## Score: 8 / 10

## Evidence

- **Source lines**: 5,179 lines across 60 Python files in `src/` — moderate size.
- **Test lines**: 4,358 lines across 39 Python files — ~0.84 test-to-source ratio.
- **Classes**: 22 in src/, 103 in tests/ (heavy test class usage).
- **No cyclic imports detected** — mypy and pytest both pass.
- **AGENTS.md**: Comprehensive architecture and principle documentation for future maintainers.
- **CONTRIBUTING.md**: Clear standards, no ambiguity.
- **Refactoring history**: CHANGELOG shows active DRY/LoD improvements (issue #100).

## Findings

### P0
None.

### P1
- **`__pycache__` directories committed** — `__pycache__/` found in file listings. Should be in `.gitignore` and removed from repo.
  - Files: `src/pinocchio_models/__pycache__/`, `tests/unit/__pycache__/`, multiple others

### P2
- **No complexity tooling** — No `radon` or `xenon` in CI to enforce cyclomatic complexity limits.
  - File: `.github/workflows/ci-standard.yml`
