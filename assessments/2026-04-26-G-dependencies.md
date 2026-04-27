# G — Dependencies (Weight: 8%)

## Score: 8 / 10

## Evidence

- **Core deps**: `numpy>=1.26.4,<3.0.0`, `matplotlib>=3.7.0` — minimal, well-scoped.
- **Optional deps**: pinocchio, gepetto, pink, crocoddyl — all isolated in extras.
- **Dev deps**: pytest, pytest-cov, pytest-mock, pytest-timeout, pytest-xdist, ruff, mypy, hypothesis, pytest-benchmark.
- **No abandoned deps**: All deps actively maintained (NumPy, Matplotlib, pytest ecosystem).
- **No compiled dep hell**: Core package is pure Python; compiled deps (pinocchio) are optional.
- **Rust core**: `pyo3` + `ndarray` + `rayon` — modern Rust stack.
- **Dependabot enabled**: Weekly scans for pip and GitHub Actions.
- **No `poetry.lock` / `requirements.txt` / `uv.lock`** — No reproducible lockfile for non-hatchling consumers.

## Findings

### P0
None.

### P1
- **No lockfile** — No pinned dependency manifest for reproducible installs. `pyproject.toml` uses lower bounds only.
  - File: `pyproject.toml`

### P2
- **NumPy upper bound `<3.0.0`** — NumPy 2.x is now stable; upper bound may block security fixes from NumPy 3.x when released. Consider evaluating NumPy 2.x compatibility.
  - File: `pyproject.toml`, line ~17
