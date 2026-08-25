"""CLI smoke tests: subcommand routing, help tree, validation (no network)."""

from __future__ import annotations

import os
import sys

from typer.testing import CliRunner

from orzmc import FileStore
from orzmc_app.cli import app

# ``orzmc_app.cli.app`` 包属性被 __init__ 重导出遮蔽成 Typer 实例,
# ``import ... as`` 走属性查找也会拿到实例;patch 必须落在真正的模块上。
app_module = sys.modules["orzmc_app.cli.app"]

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "2.0.0" in result.stdout


def test_help_lists_all_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("client", "server", "remove", "list", "backup", "version"):
        assert name in result.stdout


def test_list_empty(tmp_path) -> None:
    result = runner.invoke(app, ["list", "--root-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "尚未安装任何版本" in result.stdout


def test_list_shows_installed(tmp_path) -> None:
    fs = FileStore()
    fs.ensure_dir(os.path.join(str(tmp_path), "versions", "1.20.4", "client"))
    fs.ensure_dir(os.path.join(str(tmp_path), "versions", "1.20.4", "server", "paper"))
    result = runner.invoke(app, ["list", "--root-dir", str(tmp_path)])
    assert result.exit_code == 0
    assert "1.20.4" in result.stdout
    assert "paper" in result.stdout


def test_client_rejects_server_type() -> None:
    result = runner.invoke(app, ["client", "-t", "paper", "--version", "1.20.4"])
    assert result.exit_code == 1
    assert "不能用于客户端" in result.stdout


def test_client_rejects_unknown_type() -> None:
    result = runner.invoke(app, ["client", "-t", "spigot", "--version", "1.20.4"])
    assert result.exit_code == 1
    assert "未知类型" in result.stdout


def test_client_accepts_forge_type(monkeypatch) -> None:
    calls: list[str] = []

    def fake_resolve(version, root_dir=None):
        return version or "1.20.4"

    def fake_launch(options, **kwargs) -> None:
        calls.append("launch")

    monkeypatch.setattr(app_module, "resolve_version", fake_resolve)
    monkeypatch.setattr(app_module, "launch_client", fake_launch)
    result = runner.invoke(app, ["client", "-t", "forge", "--version", "1.20.4"])
    assert result.exit_code == 0, result.stdout
    assert calls == ["launch"]


def test_server_accepts_fabric_and_forge(monkeypatch) -> None:
    types_seen: list[str] = []

    def fake_resolve(version, root_dir=None):
        return version or "1.20.4"

    def fake_deploy(options, **kwargs) -> None:
        types_seen.append(options.game_type)

    monkeypatch.setattr(app_module, "resolve_version", fake_resolve)
    monkeypatch.setattr(app_module, "deploy_server", fake_deploy)
    for game_type in ("vanilla", "paper", "fabric", "forge"):
        result = runner.invoke(app, ["server", "-t", game_type, "--version", "1.20.4"])
        assert result.exit_code == 0, result.stdout
    assert types_seen == ["vanilla", "paper", "fabric", "forge"]


def test_remove_server_requires_type() -> None:
    result = runner.invoke(app, ["remove", "-v", "1.20.4", "--server"])
    assert result.exit_code == 1
    assert "需要指定类型" in result.stdout


def test_remove_missing_version_raises(tmp_path) -> None:
    result = runner.invoke(app, ["remove", "-v", "9.9.9", "--yes", "--root-dir", str(tmp_path)])
    assert result.exit_code == 1
    assert "未找到" in result.stdout


def test_bad_memory_rejected() -> None:
    result = runner.invoke(app, ["client", "--minmem", "huge", "--version", "1.20.4"])
    assert result.exit_code == 1
    assert "无效内存" in result.stdout
