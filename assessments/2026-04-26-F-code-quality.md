# F — Code Quality (Weight: 10%)

## Score: 9 / 10

## Evidence

- **ruff**: `All checks passed!` (ruff 0.15.12 against src/tests/scripts/examples).
- **ruff config**: line-length 88, target py310, 15 lint rule categories enabled.
- **per-file-ignores**: Appropriate (`scripts/**`, `tests/**`, `examples/**` allow `T201` print).
- **No print statements in src/**: 0 occurrences of `print(` in `src/`.
- **No bare asserts in src/**: 0 occurrences of `assert ` in `src/`.
- **mypy**: Success, no issues in 60 source files.
- **Design by Contract**: `require_*` and `ensure_*` guard functions used consistently.
- **Magic numbers extracted**: Joint limits moved to named constants (per CHANGELOG).
- **Law of Demeter**: Enforced via base class abstraction (per AGENTS.md).

## Findings

### P0
None.

### P1
None.

### P2
- **ruff version drift** — CI pins `ruff==0.14.10`, local env installed `ruff-0.15.12`. Minor but could cause inconsistent formatting/linting behavior across versions.
  - File: `.github/workflows/ci-standard.yml` line ~34 vs local install
