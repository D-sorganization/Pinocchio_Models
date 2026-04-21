"""Regression tests for CI workflow validity.

Issue #167: ci-standard.yml must not contain merge conflict markers and
must be valid YAML so that GitHub Actions can parse and execute the workflow.
"""

from __future__ import annotations

import pathlib

_REPO_ROOT = pathlib.Path(__file__).parents[2]
_CI_WORKFLOW = _REPO_ROOT / ".github" / "workflows" / "ci-standard.yml"

_CONFLICT_MARKERS = ("<<<<<<", "=======", ">>>>>>>")


def test_ci_workflow_has_no_conflict_markers() -> None:
    """Regression for #167: ci-standard.yml must not contain Git conflict markers.

    Merge conflict markers make the file invalid YAML, which prevents GitHub
    Actions from loading the workflow for push/pull_request triggers.
    """
    text = _CI_WORKFLOW.read_text(encoding="utf-8")
    found = [m for m in _CONFLICT_MARKERS if m in text]
    msg = f"Conflict markers found in ci-standard.yml: {found}"
    assert not found, msg


def test_ci_workflow_is_valid_yaml() -> None:
    """ci-standard.yml must parse as valid YAML with expected structure."""
    import yaml  # noqa: PLC0415

    text = _CI_WORKFLOW.read_text(encoding="utf-8")
    result = yaml.safe_load(text)
    assert isinstance(result, dict), "ci-standard.yml parsed to unexpected type"
    assert "jobs" in result, "ci-standard.yml is missing 'jobs' key"


def test_ci_workflow_has_required_jobs() -> None:
    """CI workflow must define quality-gate and tests jobs."""
    import yaml  # noqa: PLC0415

    text = _CI_WORKFLOW.read_text(encoding="utf-8")
    result = yaml.safe_load(text)
    jobs = result.get("jobs", {})
    assert "quality-gate" in jobs, "CI workflow is missing 'quality-gate' job"
    assert "tests" in jobs, "CI workflow is missing 'tests' job"
