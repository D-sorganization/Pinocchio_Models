# N — Accessibility (Weight: 4%)

## Score: 5 / 10

## Evidence

- **CLI accessible**: `python3 -m pinocchio_models` provides help text.
- **Documentation is text-based** — No images requiring alt text.
- **No web UI** — Pure Python library, no HTML/JS frontend to evaluate for WCAG.
- **README table formatting** — Markdown tables used for exercise list, clear structure.
- **No screen-reader considerations for CLI** — No `--quiet` or structured output modes beyond basic logging.
- **2,640 accessibility keyword matches** — Mostly from `CHANGELOG.md` "acknowledge" and `AGENTS.md` "accessible" in generic context, not a11y-specific.

## Findings

### P0
None.

### P1
None.

### P2
- **CLI output not structured** — No `--json` or `--output-format` flag for machine-readable output, limiting integration with assistive tooling or automation.
  - File: `src/pinocchio_models/__main__.py`
