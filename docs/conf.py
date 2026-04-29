"""Sphinx configuration for Pinocchio Models API documentation."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SOURCE_ROOT = PROJECT_ROOT / "src"
sys.path.insert(0, str(SOURCE_ROOT))

project = "Pinocchio Models"
copyright = "2026, D-sorganization"
author = "D-sorganization"

extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.napoleon",
]

autodoc_default_options = {
    "members": True,
    "show-inheritance": True,
}
autodoc_typehints = "description"

templates_path = ["_templates"]
exclude_patterns = ["_build", "Thumbs.db", ".DS_Store"]

html_theme = "alabaster"
html_static_path = []
