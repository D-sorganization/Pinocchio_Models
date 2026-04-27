# O — Agentic Usability (Weight: 3%)

## Score: 9 / 10

## Evidence

- **AGENTS.md**: Comprehensive (50+ lines) covering safety, Python standards, architecture, DbC, TDD, DRY, LoD.
- **CLAUDE.md**: Present — Claude-specific instructions.
- **SPEC.md**: Canonical spec with identity, purpose, goals/non-goals, entrypoints, validation rules.
- **No TODO/FIXME in committed code**: CI explicitly fails on placeholders.
- **Self-documenting code**: Type hints, docstrings, named constants.
- **CI enforces standards**: ruff, mypy, bandit, placeholder scan all automated.

## Findings

### P0
None.

### P1
None.

### P2
- **No `.cursorrules` or `.clinerules`** — No IDE-specific agent context files beyond `CLAUDE.md` and `AGENTS.md`.
  - File: project root
