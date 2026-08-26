"""Interactive TTY prompts for the CLI (only used when stdin is a TTY)."""

from __future__ import annotations

import sys

from rich.console import Console
from rich.prompt import Confirm

from orzmc import remote_version_catalog

from .picker import run_picker

_console = Console(highlight=False)


def is_interactive() -> bool:
    """True when stdin+stdout are real terminals (safe for rich prompts)."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def resolve_version(version: str | None, root_dir: str | None) -> str | None:
    """Resolve the Minecraft version for a command.

    Explicit value → used as-is. TTY without value → interactive keyboard
    picker over the full Mojang catalog (scroll, filter, release/snapshot
    toggle, Escape → latest). Non-TTY without value → ``None``, letting the
    library fall back to the latest release.
    """
    if version:
        return version
    if not is_interactive():
        return None
    try:
        catalog = remote_version_catalog(root_dir=root_dir)
    except Exception as exc:
        _console.print(f"[yellow]无法获取版本列表({exc}),回车使用最新[/yellow]")
        return None
    if not catalog:
        _console.print("[yellow]版本清单为空,回车使用最新[/yellow]")
        return None
    try:
        return run_picker(catalog)
    except Exception as exc:  # never crash the CLI on TUI trouble
        _console.print(f"[yellow]版本选择器异常({exc}),回车使用最新[/yellow]")
        return None


def confirm_java(major: int, need_jdk: bool) -> bool:
    """Ask before installing a sandboxed Java runtime into the app dir."""
    kind = "JDK" if need_jdk else "JRE"
    return Confirm.ask(f"需要安装 Java {major}({kind}) 到应用目录,继续?", default=True)


def confirm_eula() -> bool:
    """Ask the user to accept the Minecraft EULA before starting a server."""
    return Confirm.ask("需要接受 Minecraft EULA 才能启动服务端,是否同意?", default=True)
