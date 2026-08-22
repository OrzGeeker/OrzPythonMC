"""Interactive TTY prompts for the CLI (only used when stdin is a TTY)."""

from __future__ import annotations

import sys

from rich.console import Console
from rich.prompt import Confirm, Prompt

from orzmc import remote_versions

_console = Console(highlight=False)


def is_interactive() -> bool:
    """True when stdin+stdout are real terminals (safe for rich prompts)."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def resolve_version(version: str | None, root_dir: str | None) -> str | None:
    """Resolve the Minecraft version for a command.

    Explicit value → used as-is. TTY without value → interactive pick from the
    recent Mojang releases. Non-TTY without value → ``None``, letting the
    library fall back to the latest release.
    """
    if version:
        return version
    if not is_interactive():
        return None
    try:
        releases = remote_versions(root_dir=root_dir)
    except Exception as exc:
        _console.print(f"[yellow]无法获取版本列表({exc}),回车使用最新[/yellow]")
        return None
    if not releases:
        return None
    recent = releases[:15]
    _console.print("[info]最近的 Mojang release:[/info]")
    for i, item in enumerate(recent[:10], 1):
        _console.print(f"  [muted]{i:>2}.[/muted] {item}")
    picked = Prompt.ask("选择版本(输入序号/版本号,回车用最新)", default="")
    picked = picked.strip()
    if not picked:
        return None
    if picked.isdigit() and 1 <= int(picked) <= len(recent):
        return recent[int(picked) - 1]
    return picked


def confirm_java(major: int, need_jdk: bool) -> bool:
    """Ask before installing a sandboxed Java runtime into the app dir."""
    kind = "JDK" if need_jdk else "JRE"
    return Confirm.ask(f"需要安装 Java {major}({kind}) 到应用目录,继续?", default=True)


def confirm_eula() -> bool:
    """Ask the user to accept the Minecraft EULA before starting a server."""
    return Confirm.ask("需要接受 Minecraft EULA 才能启动服务端,是否同意?", default=True)
