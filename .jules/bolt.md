## 2024-05-19 - Precondition Performance Bottleneck
**Learning:** The `require_finite` precondition function in `src/pinocchio_models/shared/contracts/preconditions.py` was a significant performance bottleneck during URDF generation. It converted all inputs (even simple Python scalars) to numpy arrays using `np.asarray` and used `np.all(np.isfinite())`. For tight loops dealing mostly with scalars, this creates massive overhead.
**Action:** When implementing preconditions or validation logic that handles both scalars and arrays, always add a fast path for built-in scalars (e.g., `isinstance(arr, (int, float))`) using Python's built-in `math.isfinite`. Only fall back to numpy for actual array inputs.

## 2024-05-18 - Optimize URDF Float Formatting
**Learning:** In URDF XML generation for robotics, printing exact zeros (`0.0`) using Python f-strings like `f"{x:.6f}"` creates a large overhead and balloons file size unnecessarily with outputs like `"0.000000"`.
**Action:** Always short-circuit exact zero floats to `"0"` and use a helper string formatting method, which speeds up model generation and reduces file parsing overhead downstream.

## 2026-04-22 - Redundant XML Serialization Bottleneck
**Learning:** In the model generation pipeline (`src/pinocchio_models/exercises/base.py`), the URDF postcondition validation (`ensure_valid_urdf`) was a bottleneck. It was converting the `ET.Element` tree to a string and then immediately parsing it back into an `ET.Element` tree just to perform validation checks.
**Action:** Validate the `xml.etree.ElementTree.Element` tree directly in memory before serialization using a dedicated function (`ensure_valid_urdf_tree`), completely skipping the redundant string parsing overhead.

## 2026-04-24 - Tight Loop XML Tag Validation Optimization
**Learning:** During in-memory URDF validation (`ensure_valid_urdf_tree`), the regex pattern `r"^[a-zA-Z_][a-zA-Z0-9_\-\.]*$"` was being repeatedly compiled and `isinstance(el.tag, str)` evaluated for thousands of XML tags. Profiling revealed `isinstance` and method lookups accounted for significant overhead.
**Action:** For tight loops, hoist `re.compile()` to the module level, pre-resolve method references like `_VALID_TAG_MATCH = _VALID_TAG_PATTERN.match`, and swap `isinstance(tag, str)` with a faster `type(tag) is str` check.
