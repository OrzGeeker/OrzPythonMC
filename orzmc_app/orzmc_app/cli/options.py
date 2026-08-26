"""Shared typer option declarations reused across CLI subcommands."""

from __future__ import annotations

from typing import Annotated

import typer

# ── generic ──────────────────────────────────────────────────────────────────


def _root_dir_help() -> str:
    return "游戏根目录(默认 ~/minecraft)"


def _version_help() -> str:
    return "Minecraft 版本(缺省:TTY 交互选择,可搜索/切换正式版·测试版;非 TTY 用 Mojang 最新 release)"


# ── option type aliases ──────────────────────────────────────────────────────

RootDir = Annotated[str | None, typer.Option("--root-dir", help=_root_dir_help())]
Version = Annotated[str | None, typer.Option("--version", "-v", help=_version_help())]
Username = Annotated[str, typer.Option("--username", "-u", help="游戏用户名(默认 guest)")]
MinMem = Annotated[str, typer.Option("--minmem", "-m", help="最小内存(如 512M)")]
MaxMem = Annotated[str, typer.Option("--maxmem", "-x", help="最大内存(如 2G)")]
JvmOpts = Annotated[str | None, typer.Option("--jvm-opts", help="附加 JVM 旗标(空格分隔,如 '-XX:+UseZGC')")]
Verbose = Annotated[bool, typer.Option("--verbose", help="输出调试日志")]
Yes = Annotated[bool, typer.Option("--yes", help="跳过交互确认(自动接受 EULA 等)")]
