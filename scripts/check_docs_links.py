"""Validate local Markdown links in repository documentation."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC_GLOBS = ("*.md", "docs/**/*.md")
MARKDOWN_LINK_RE = re.compile(r"(?<!!)\[[^\]]+\]\(([^)]+)\)")


def _iter_markdown_files() -> list[Path]:
    """Return tracked documentation locations checked by this script."""
    files: set[Path] = set()
    for pattern in DOC_GLOBS:
        files.update(REPO_ROOT.glob(pattern))
    return sorted(path for path in files if path.is_file())


def _is_local_link(target: str) -> bool:
    """Return whether *target* should resolve to a local repository path."""
    return not (
        target.startswith(("http://", "https://", "mailto:", "#")) or "://" in target
    )


def _resolve_link(markdown_file: Path, target: str) -> Path:
    """Resolve a Markdown link target relative to *markdown_file*."""
    clean_target = target.split("#", 1)[0]
    return (markdown_file.parent / clean_target).resolve()


def find_broken_links() -> list[str]:
    """Return formatted diagnostics for local Markdown links that do not exist."""
    broken: list[str] = []
    for markdown_file in _iter_markdown_files():
        text = markdown_file.read_text(encoding="utf-8")
        for match in MARKDOWN_LINK_RE.finditer(text):
            target = match.group(1).strip()
            if not target or not _is_local_link(target):
                continue
            resolved = _resolve_link(markdown_file, target)
            if not resolved.exists():
                rel_file = markdown_file.relative_to(REPO_ROOT)
                broken.append(f"{rel_file}: missing link target {target}")
    return broken


def main() -> int:
    """Run the documentation link check."""
    broken = find_broken_links()
    if broken:
        print("Broken documentation links:")
        for item in broken:
            print(f"- {item}")
        return 1
    print("Documentation links OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
