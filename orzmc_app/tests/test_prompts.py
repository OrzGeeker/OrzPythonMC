"""resolve_version wiring: explicit value / non-TTY / picker call / fallbacks, no TTY/network."""

from __future__ import annotations

from orzmc import VersionEntry
from orzmc_app.cli import prompts as prompts_module
from orzmc_app.cli.prompts import resolve_version

CATALOG = [
    VersionEntry("1.21.4", "release"),
    VersionEntry("1.21.3", "release"),
    VersionEntry("1.20.4", "release"),
    VersionEntry("25w14a", "snapshot"),
    VersionEntry("b1.7.3", "old_beta"),
    VersionEntry("c0.0.13a", "old_alpha"),
]


class TestResolveVersion:
    def test_explicit_version_skips_prompt(self) -> None:
        assert resolve_version("1.20.4", None) == "1.20.4"

    def test_non_interactive_returns_none(self, monkeypatch) -> None:
        monkeypatch.setattr(prompts_module, "is_interactive", lambda: False)
        assert resolve_version(None, None) is None

    def test_tty_calls_picker(self, monkeypatch) -> None:
        monkeypatch.setattr(prompts_module, "is_interactive", lambda: True)
        monkeypatch.setattr(prompts_module, "remote_version_catalog", lambda root_dir=None: CATALOG)
        monkeypatch.setattr(prompts_module, "run_picker", lambda catalog: "1.21.4")
        assert resolve_version(None, None) == "1.21.4"

    def test_picker_none_falls_back_to_latest(self, monkeypatch) -> None:
        # Escape in the picker returns None → caller falls back to latest release.
        monkeypatch.setattr(prompts_module, "is_interactive", lambda: True)
        monkeypatch.setattr(prompts_module, "remote_version_catalog", lambda root_dir=None: CATALOG)
        monkeypatch.setattr(prompts_module, "run_picker", lambda catalog: None)
        assert resolve_version(None, None) is None

    def test_picker_exception_falls_back(self, monkeypatch) -> None:
        monkeypatch.setattr(prompts_module, "is_interactive", lambda: True)
        monkeypatch.setattr(prompts_module, "remote_version_catalog", lambda root_dir=None: CATALOG)

        def boom(catalog):
            raise RuntimeError("选择器故障")

        monkeypatch.setattr(prompts_module, "run_picker", boom)
        assert resolve_version(None, None) is None

    def test_network_failure_falls_back(self, monkeypatch) -> None:
        monkeypatch.setattr(prompts_module, "is_interactive", lambda: True)

        def boom(root_dir=None):
            raise RuntimeError("网络错误")

        monkeypatch.setattr(prompts_module, "remote_version_catalog", boom)
        assert resolve_version(None, None) is None

    def test_empty_catalog_falls_back(self, monkeypatch) -> None:
        monkeypatch.setattr(prompts_module, "is_interactive", lambda: True)
        monkeypatch.setattr(prompts_module, "remote_version_catalog", lambda root_dir=None: [])
        assert resolve_version(None, None) is None
