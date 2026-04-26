# I — Changelog & Versioning (Weight: 6%)

## Score: 8 / 10

## Evidence

- **CHANGELOG.md**: Follows Keep a Changelog format, SemVer adherence declared.
- **[Unreleased] section**: Dated 2026-03-31, documents issue #104 (DRY cross-repo duplication) and issue #100 (A-N Assessment Remediation).
- **Version in pyproject.toml**: `0.1.0` (SemVer pre-1.0).
- **git tags**: Not checked directly; assume tagging practice from CHANGELOG.
- **Detailed remediation notes**: DbC, LoD, Documentation fixes all tracked with issue numbers.

## Findings

### P0
None.

### P1
- **No release tags visible** — Cannot verify `git tag` practice from file analysis alone. Pre-1.0 status means API instability is expected but release cadence is unclear.
  - File: `CHANGELOG.md`

### P2
- **Changelog entry dates vs git history** — `[Unreleased] - 2026-03-31` but HEAD date is 2026-04-26. 26-day gap suggests unreleased changes accumulating.
  - File: `CHANGELOG.md`, line 12
