# Contributing to Pinocchio Models

Thank you for your interest in contributing!

## Getting Started

1. Fork the repository.
2. Clone your fork and create a feature branch from `main`.
3. Install development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

## Development Workflow

- **Lint:** `ruff check src scripts tests examples`
- **Format:** `ruff format src scripts tests examples`
- **Type check:** `mypy src --config-file pyproject.toml`
- **Test:** `python3 -m pytest tests/ -v --tb=short`

All four must pass before submitting a PR.

## Code Standards

- Use `python3`, never `python`.
- Type hints on all public function signatures.
- Design by Contract: validate inputs with `require_*`, outputs with `ensure_*`.
- No `TODO`/`FIXME` in committed code unless linked to a tracked GitHub issue.

## Pull Requests

- Keep PRs focused on a single concern.
- All CI checks must pass before merge.
- Never use `--admin` to bypass checks.

## Reporting Issues

Open a GitHub issue with a clear description and reproduction steps.
