# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| 0.1.x   | Yes       |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue.
2. Email the maintainers at the address listed in the repository.
3. Include a description of the vulnerability and steps to reproduce.
4. We will acknowledge receipt within 48 hours and provide a timeline for a fix.

## Security Measures

- Dependencies are audited with `pip-audit` and `bandit` in CI.
- Dependabot is enabled for automated dependency updates.
- All PRs require passing CI checks before merge.
