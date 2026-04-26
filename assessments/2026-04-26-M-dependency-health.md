# M — Dependency Health (Weight: 5%)

## Score: 7 / 10

## Evidence

- **Core deps**: numpy 1.26.4+, matplotlib 3.7+ — both stable, well-maintained.
- **Optional deps**: pinocchio, gepetto, pink, crocoddyl — all domain-specific, maintained.
- **Dev deps**: Modern pytest 9.x, ruff 0.14+, mypy 1.13+.
- **Dependabot**: Weekly scans for pip and GitHub Actions.
- **pip-audit**: Runs in CI with 6 ignored CVEs.
- **No outdated dependency dashboard** — No explicit dependency age tracking.

## Findings

### P0
None.

### P1
- **6 CVEs ignored without remediation plan** — Same as criteria E and H. Dependency health requires active CVE management.
  - File: `.github/workflows/ci-standard.yml`, lines 82–87

### P2
- **No dependency age tracking** — No Renovate or dependency freshness metrics.
