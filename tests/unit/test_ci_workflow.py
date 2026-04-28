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
    """CI workflow must define required CI jobs."""
    import yaml  # noqa: PLC0415

    text = _CI_WORKFLOW.read_text(encoding="utf-8")
    result = yaml.safe_load(text)
    jobs = result.get("jobs", {})
    assert "quality-gate" in jobs, "CI workflow is missing 'quality-gate' job"
    assert "tests" in jobs, "CI workflow is missing 'tests' job"
    assert "profiling" in jobs, "CI workflow is missing 'profiling' job"


def test_ci_workflow_profiles_on_schedule_or_manual_only() -> None:
    """Regression for #201: profiling is available without slowing PR CI."""
    import yaml  # noqa: PLC0415

    text = _CI_WORKFLOW.read_text(encoding="utf-8")
    result = yaml.safe_load(text)
    triggers = result.get("on", result.get(True, {}))
    profiling = result["jobs"]["profiling"]

    assert "schedule" in triggers, "CI workflow is missing a scheduled trigger"
    assert "workflow_dispatch" in triggers, "CI workflow is missing manual trigger"
    assert (
        profiling["if"]
        == "github.event_name == 'schedule' || github.event_name == 'workflow_dispatch'"
    )


def test_ci_workflow_uploads_line_profiler_report() -> None:
    """Profiling job must produce and upload line_profiler report artifacts."""
    import yaml  # noqa: PLC0415

    text = _CI_WORKFLOW.read_text(encoding="utf-8")
    result = yaml.safe_load(text)
    steps = result["jobs"]["profiling"]["steps"]
    run_blocks = "\n".join(step.get("run", "") for step in steps)
    artifact_steps = [
        step for step in steps if step.get("uses") == "actions/upload-artifact@v4"
    ]

    assert "python3 -m kernprof" in run_blocks
    assert "python3 -m line_profiler" in run_blocks
    assert "profiling/model-generation.lprof" in run_blocks
    assert "profiling/model-generation-line-profiler.txt" in run_blocks
    assert artifact_steps, "profiling job must upload the line_profiler reports"
