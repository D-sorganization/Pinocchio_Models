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
## 2024-05-18 - Optimize Float string caching URDF formatting
**Learning:** Formatting float numbers with `f"{x:.6f}"` creates significant repeated overhead during tree generation for frequently accessed values like 0.0 or duplicate coordinates.
**Action:** The string result of `float_str` should be cached via `@lru_cache(maxsize=1024)` in `urdf_helpers.py` so identical numbers don't require recomputing their exact string representation.

## 2026-04-30 - Optimize URDF Vector3 Formatting
**Learning:** Formatting float numbers to Vector3 strings (e.g. `0 0 0`) dynamically creates significant repeated overhead during tree generation for frequently accessed coordinates. Even though individual floats might be cached, string interpolation (`f"{float_str(x)} {float_str(y)} {float_str(z)}"`) scales poorly.
**Action:** The string result of `vec3_str` should be cached via `@lru_cache(maxsize=1024)` in `urdf_helpers.py` so shared coordinates across joints don't require recomputing their exact string representation.

## 2026-05-01 - Optimize Precondition Validation Type Checking
**Learning:** In tight loops like `require_finite` inside `src/robotics_contracts/preconditions.py`, checking for primitive and numpy scalar types using `isinstance` adds notable overhead. Specifically, falling back to `np.asarray()` for numpy scalar types (e.g. `np.float64`) because `isinstance(arr, (int, float))` fails for them takes significantly longer than using the built-in `math.isfinite()`.
**Action:** Use exact type checking (e.g., `type(arr) is float` or `type(arr) is np.float64`) over `isinstance()` for primitive types and numpy scalars in hot paths to bypass the slow `np.asarray()` conversion. This dramatically improves performance while maintaining safety.
