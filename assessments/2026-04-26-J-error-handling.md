# J — Error Handling (Weight: 7%)

## Score: 8 / 10

## Evidence

- **40 `raise` statements** in `src/` — active error signaling.
- **15 `try:` blocks**, **11 `except` clauses** — structured exception handling.
- **26 logging references** in `src/` — `logging` module used (not print).
- **Design by Contract**: `require_*` guards for preconditions, `ensure_*` for postconditions.
- **Specific exception types**: `ValueError` for invalid inputs, `AssertionError` replaced with `ValueError` per CHANGELOG.
- **CLI validation**: `--mass`, `--height`, `--plates` validated in `__main__.py` (issue #100 remediation).

## Findings

### P0
None.

### P1
- **Some exception messages lack context** — `ValueError` raised without structured error codes or machine-readable identifiers. Makes programmatic error handling harder.
  - Files: `src/pinocchio_models/shared/contracts/preconditions.py`, `src/pinocchio_models/shared/contracts/postconditions.py`

### P2
- **No structured error taxonomy** — No custom exception hierarchy (e.g., `PinocchioModelsError`, `GeometryError`, `URDFError`). All errors use built-in types.
  - Files: entire `src/` tree
