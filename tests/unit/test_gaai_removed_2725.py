"""The vendored GAAI framework is gone and must not come back.

The owner retired GAAI fleet-wide (Repository_Management#2725). The checked-in
``.gaai/`` tree is removed; these checks keep it, any launcher script, and live
pointers to it from returning.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

pytestmark = pytest.mark.unit

REPO_ROOT = Path(__file__).resolve().parents[2]

# Files an agent or tool reads on every run, plus the live status doc. A GAAI
# pointer here would send a reader to files that no longer exist.
LIVE_ENTRY_POINTS = (
    "CLAUDE.md",
    "AGENTS.md",
    "README.md",
    ".gitignore",
    "docs/project/STATUS.md",
)

_GAAI = re.compile(r"gaai", re.IGNORECASE)


def test_vendored_tree_is_removed() -> None:
    assert not (REPO_ROOT / ".gaai").exists()


def test_no_gaai_launcher_script_exists() -> None:
    skip = {".git", ".venv", "node_modules", "target"}
    found = [
        str(path.relative_to(REPO_ROOT))
        for path in REPO_ROOT.rglob("*")
        if _GAAI.search(path.name)
        and path.is_file()
        and not skip.intersection(path.relative_to(REPO_ROOT).parts)
        and path.parent.name != "changes"
        and path != Path(__file__).resolve()
    ]
    assert found == []


@pytest.mark.parametrize("relative_path", LIVE_ENTRY_POINTS)
def test_live_entry_point_does_not_mention_gaai(relative_path: str) -> None:
    path = REPO_ROOT / relative_path
    assert path.is_file(), f"{relative_path} moved -- update LIVE_ENTRY_POINTS"
    hits = [
        f"{relative_path}:{number}"
        for number, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        )
        if _GAAI.search(line)
    ]
    assert hits == []
