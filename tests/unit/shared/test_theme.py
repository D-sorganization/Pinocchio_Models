"""Tests for shared plotting theme import and fallback behavior."""

from __future__ import annotations

import importlib
import sys
from types import ModuleType, SimpleNamespace
from unittest.mock import patch


class TestSharedTheme:
    def test_uses_plot_theme_when_available(self) -> None:
        import pinocchio_models.shared.theme as theme_mod

        plot_theme_pkg = ModuleType("plot_theme")
        plot_theme_pkg.__path__ = []  # type: ignore[attr-defined]

        calls: list[object] = []
        fake_theme = SimpleNamespace(name="codex-test-theme")

        integration_mod = ModuleType("plot_theme.integration")
        integration_mod.style_axis = lambda ax: calls.append(ax)

        themes_mod = ModuleType("plot_theme.themes")
        themes_mod.DEFAULT_THEME = "codex"
        themes_mod.get_theme = lambda name: fake_theme if name == "codex" else None

        with patch.dict(
            sys.modules,
            {
                "plot_theme": plot_theme_pkg,
                "plot_theme.integration": integration_mod,
                "plot_theme.themes": themes_mod,
            },
        ):
            theme_mod = importlib.reload(theme_mod)

            assert theme_mod.theme is fake_theme
            marker = object()
            theme_mod.style_axis(marker)
            assert calls == [marker]

    def test_falls_back_to_noop_when_plot_theme_is_missing(self) -> None:
        import pinocchio_models.shared.theme as theme_mod

        plot_theme_pkg = ModuleType("plot_theme")
        plot_theme_pkg.__path__ = []  # type: ignore[attr-defined]

        with patch.dict(
            sys.modules,
            {
                "plot_theme": plot_theme_pkg,
                "plot_theme.integration": None,
                "plot_theme.themes": None,
            },
        ):
            theme_mod = importlib.reload(theme_mod)

            assert theme_mod.theme is None
            assert theme_mod.style_axis(object()) is None
