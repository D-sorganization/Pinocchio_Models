"""Regression tests for auditable pip-audit vulnerability ignores."""

from __future__ import annotations

import pathlib
import re

import yaml

_REPO_ROOT = pathlib.Path(__file__).parents[2]
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci-standard.yml"
_IGNORE_TRACKING = _REPO_ROOT / "docs" / "security" / "pip_audit_ignores.yml"

_IGNORE_PATTERN = re.compile(r"--ignore-vuln\s+(CVE-\d{4}-\d+)")
_REQUIRED_FIELDS = {
    "dependency",
    "root_cause",
    "patched_versions",
    "remediation_timeline",
    "removal_criteria",
    "tracking_issue",
}


def _workflow_ignores() -> set[str]:
    return set(_IGNORE_PATTERN.findall(_CI_WORKFLOW.read_text(encoding="utf-8")))


def _tracked_ignores() -> dict[str, dict[str, object]]:
    loaded = yaml.safe_load(_IGNORE_TRACKING.read_text(encoding="utf-8"))
    assert isinstance(loaded, dict), "pip-audit ignore tracking must be a mapping"
    entries = loaded.get("ignored_vulnerabilities")
    assert isinstance(entries, list), "ignored_vulnerabilities must be a list"

    tracked: dict[str, dict[str, object]] = {}
    for entry in entries:
        assert isinstance(entry, dict), "each ignored vulnerability must be a mapping"
        cve_id = entry.get("id")
        assert isinstance(cve_id, str), "each ignored vulnerability needs an id"
        assert cve_id not in tracked, f"duplicate ignore tracking entry for {cve_id}"
        tracked[cve_id] = entry
    return tracked


def test_every_workflow_pip_audit_ignore_is_tracked() -> None:
    """Every --ignore-vuln flag must have a tracked remediation entry."""
    workflow_ignores = _workflow_ignores()
    tracked_ignores = set(_tracked_ignores())

    assert workflow_ignores, "workflow should still expose explicit pip-audit ignores"
    assert workflow_ignores <= tracked_ignores


def test_tracked_pip_audit_ignores_have_remediation_metadata() -> None:
    """Tracked ignores must identify root cause, dependency, and removal path."""
    for cve_id, entry in _tracked_ignores().items():
        missing = _REQUIRED_FIELDS - set(entry)
        assert not missing, f"{cve_id} is missing fields: {sorted(missing)}"

        for field in _REQUIRED_FIELDS - {"patched_versions"}:
            value = entry[field]
            assert isinstance(value, str), f"{cve_id}.{field} must be a string"
            assert value.strip(), f"{cve_id}.{field} must not be blank"

        patched_versions = entry["patched_versions"]
        assert isinstance(patched_versions, list), (
            f"{cve_id}.patched_versions must be a list"
        )
        assert patched_versions, f"{cve_id}.patched_versions must not be empty"
