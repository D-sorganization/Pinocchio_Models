"""Root conftest for pytest.

Enforces fleet testing standards
(Repository_Management/docs/FLEET_TESTING_STANDARDS.md §5):
- C-extension thread-safety env vars are pinned BEFORE any heavy import.
- Headless backends (matplotlib / Qt) are pinned BEFORE any heavy import.
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Fleet Testing Standards §5 -- env vars MUST be set before heavy imports.
# ---------------------------------------------------------------------------
import os

# C-extension thread safety. Many "xdist worker crashed" failures
# come from MKL/OpenBLAS forking under xdist. Pin to single-threaded
# for tests; production code can re-thread itself if it needs to.
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")
os.environ.setdefault("NUMEXPR_NUM_THREADS", "1")

# matplotlib headless backend, set before any matplotlib import.
os.environ.setdefault("MPLBACKEND", "Agg")

# Qt headless backend, for repos that import PyQt/PySide indirectly.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
