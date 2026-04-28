# Performance Budget

This document defines the model-generation latency SLO for
`Pinocchio_Models`. It closes the assessment gap where benchmark tests existed
without a threshold or documented response policy.

## Scope

The budget applies to the core, dependency-light model builders exercised by
`tests/benchmarks/test_model_generation_benchmark.py`:

- `squat`
- `bench_press`
- `deadlift`
- `snatch`
- `clean_and_jerk`

Optional addon workflows for Gepetto, Pink, Crocoddyl, and downstream Pinocchio
loading are out of scope for this budget because they depend on external native
packages and runtime configuration.

## SLO

The canonical budget is stored in
[`performance_budget.yml`](performance_budget.yml). For each target builder,
single-call model generation should remain below the configured p95 threshold
when measured through the benchmark command in that file.

The current threshold is intentionally conservative. It is meant to catch
structural regressions, not normal workstation noise. Tightening the threshold
should be done only after several scheduled profiling artifacts establish a
stable runner baseline.

## Validation

Pull request CI validates that the budget artifact is parseable, contains all
required fields, and covers the same target set as the benchmark and profiling
workloads. Scheduled or manual profiling runs provide the timing evidence used
to investigate warnings and breaches.

## Breach Response

When a benchmark or profiling run exceeds `warn_at_ms`, compare the run against
the most recent successful scheduled profiling artifact. When a run exceeds
`threshold_ms`, treat the regression as a release blocker until the cause is
understood, the implementation is fixed, or the budget is intentionally revised
with supporting evidence.
