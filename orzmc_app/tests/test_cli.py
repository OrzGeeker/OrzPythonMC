"""CLI smoke tests: subcommand routing, help tree, validation (no network)."""

from __future__ import annotations

import os

from typer.testing import CliRunner

from orzmc import FileStore
from orzmc_app.cli.app import app

runner = CliRunner()


def test_version() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert "2.0.0" in result.stdout


def test_help_lists_all_commands() -> None:
    result = runner.invoke(app, ["--help"])
    assert result.exit_code == 0
    for name in ("client", "server", "remove", "list", "backup", "tui", "version"):
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
