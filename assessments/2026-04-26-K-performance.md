# K — Performance (Weight: 7%)

## Score: 7 / 10

## Evidence

- **Benchmark tests**: 5 model-generation benchmarks in `tests/benchmarks/test_model_generation_benchmark.py`.
- **Rust core**: `rust_core/` with `rayon` parallelization, `ndarray`, `pyo3` bindings.
- **CI timeout**: 15 minutes per job, 60s pytest timeout.
- **pytest-xdist**: Parallel test execution with `-n auto`.
- **No profiling artifacts**: No `cProfile`, `line_profiler`, or `scalene` integration in CI.
- **Benchmarks disabled in CI**: `pytest_benchmark` warns that xdist disables benchmarks.

## Findings

### P0
None.

### P1
- **Benchmarks never run in CI** — `pytest-xdist` automatically disables `pytest-benchmark`. Performance regressions go undetected.
  - File: `tests/benchmarks/test_model_generation_benchmark.py`

### P2
- **No profiling integration** — No automated profiling reports or flamegraphs generated in CI.
- **No performance budget** — No SLO or latency threshold defined for model generation.
