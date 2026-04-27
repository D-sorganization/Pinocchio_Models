# H — Security (Weight: 10%)

## Score: 6 / 10

## Evidence

- **SECURITY.md**: Supported versions table, responsible disclosure process, 48-hour ack SLA.
- **CI security scans**: bandit (B608, B102, etc.), pip-audit with CVE ignore list.
- **No secrets in source**: No `password`, `secret`, `token`, `api_key` patterns found in src/.
- **Dockerfile**: Non-root user (`athlete`), multi-stage build reduces attack surface.
- **6 CVEs ignored in CI** without visible remediation plan:
  - CVE-2026-4539, CVE-2026-32274, CVE-2026-21883, CVE-2026-27205, CVE-2024-47081, CVE-2026-25645
- **No SBOM generation** — No `cyclonedx-bom` or similar in CI.
- **No code signing** — Releases not signed.
- **No dependency review action** — No `actions/dependency-review-action` on PRs.

## Findings

### P0
None.

### P1
- **6 ignored CVEs lack tracked remediation issues** — Security debt is invisible. Each ignored CVE should have an open issue with timeline.
  - File: `.github/workflows/ci-standard.yml`, lines 82–87

### P2
- **No SBOM** — Supply chain visibility limited.
- **No dependency review on PRs** — New vulnerabilities in dependencies not flagged at PR time.
