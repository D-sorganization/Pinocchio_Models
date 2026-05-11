"""Model-pack manifest entry point for UpstreamDrift integration.

Implements the ``model_pack/v1`` contract registered under
``[project.entry-points."biomech.model_pack"]`` so the UpstreamDrift
launcher can discover this package without importing exercise modules.

See ``model_pack.yaml`` at the repo root for the canonical manifest and
the schema reference in
``D-sorganization/UpstreamDrift#5199``
(``src/shared/python/biomech/schemas/model_pack_v1.json``).
"""

from __future__ import annotations

from importlib import resources
from pathlib import Path
from typing import Any

import yaml

_MANIFEST_FILENAME: str = "model_pack.yaml"


def _load_manifest_text() -> str:
    """Return the raw text of the packaged ``model_pack.yaml``.

    The manifest is shipped inside the wheel via ``[tool.hatch.build]``
    so ``importlib.resources`` resolves it whether the package is
    installed normally or in editable mode.
    """
    pkg = resources.files("pinocchio_models")
    candidate = pkg / _MANIFEST_FILENAME
    if candidate.is_file():
        return candidate.read_text(encoding="utf-8")
    # Editable install / source checkout fallback: walk up from the
    # package directory to find the repo-root manifest.
    pkg_path = Path(str(pkg)).resolve()
    for parent in (pkg_path, *pkg_path.parents):
        repo_manifest = parent / _MANIFEST_FILENAME
        if repo_manifest.is_file():
            return repo_manifest.read_text(encoding="utf-8")
    raise FileNotFoundError(
        f"Could not locate {_MANIFEST_FILENAME} alongside pinocchio_models."
    )


def manifest() -> dict[str, Any]:
    """Return the parsed ``model_pack.yaml`` manifest as a dictionary.

    Returns:
        Parsed manifest with at minimum the keys declared in the
        ``model_pack/v1`` schema: ``schema``, ``repo``, ``package``,
        ``engine``, ``engine_version``, ``format``, ``models_root``,
        ``exercises``.
    """
    data = yaml.safe_load(_load_manifest_text())
    if not isinstance(data, dict):
        raise ValueError(f"{_MANIFEST_FILENAME} must contain a YAML mapping")
    return data


def resolve() -> Path:
    """Return the absolute path to the directory containing exercise models.

    The path is the ``models_root`` declared in ``model_pack.yaml``,
    resolved against the repository root (one level above the
    ``pinocchio_models`` package directory in editable installs, or the
    package directory itself in wheel installs that ship exercises).
    """
    data = manifest()
    models_root = data.get("models_root")
    if not isinstance(models_root, str) or not models_root:
        raise ValueError("manifest is missing a non-empty 'models_root' entry")

    pkg = resources.files("pinocchio_models")
    pkg_path = Path(str(pkg)).resolve()

    # Search upward for a directory containing the declared models_root.
    for parent in (pkg_path, *pkg_path.parents):
        candidate = parent / models_root
        if candidate.is_dir():
            return candidate.resolve()

    # Final fallback: package-local ``exercises/`` directory (wheel layout).
    fallback = pkg_path / "exercises"
    if fallback.is_dir():
        return fallback.resolve()
    raise FileNotFoundError(
        f"models_root '{models_root}' could not be resolved from {pkg_path}"
    )


def list_exercises() -> list[str]:
    """Return the ordered list of exercise IDs declared in the manifest."""
    data = manifest()
    exercises = data.get("exercises", [])
    if not isinstance(exercises, list):
        raise ValueError("manifest 'exercises' entry must be a list")
    out: list[str] = []
    for entry in exercises:
        if not isinstance(entry, dict):
            raise ValueError("each exercise entry must be a mapping")
        exercise_id = entry.get("id")
        if not isinstance(exercise_id, str) or not exercise_id:
            raise ValueError("each exercise entry requires a non-empty 'id'")
        out.append(exercise_id)
    return out


__all__ = ["list_exercises", "manifest", "resolve"]
