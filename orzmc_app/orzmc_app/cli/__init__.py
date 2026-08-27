"""Typer CLI entry point for orzmc-app.

The console script ``orzmc`` maps to :func:`main`.
"""

from __future__ import annotations

import sys

import typer

from orzmc_app.cli.app import app


def _reconfigure_utf8(stream: object) -> None:
    """把单个标准流重配置为 UTF-8;不可重配置 / 出错则静默跳过。"""
    reconfigure = getattr(stream, "reconfigure", None)
    if reconfigure is None:
        return
    try:
        reconfigure(encoding="utf-8", errors="replace")
    except (ValueError, OSError):
        pass


def _force_utf8_stdio() -> None:
    """Windows 下 stdout/stderr 被重定向时按 ANSI 代码页(如 cp1252)编码,
    打印中文会 UnicodeEncodeError(crash)。强制 UTF-8,管道 / 重定向输出不崩。
    交互终端不受影响(console 本就按 UTF-8 处理,见 PEP 528)。"""
    _reconfigure_utf8(sys.stdout)
    _reconfigure_utf8(sys.stderr)


def main() -> int:
    _force_utf8_stdio()
    try:
        app()
        return 0
    except typer.Exit as exc:
        return exc.exit_code or 0
    except KeyboardInterrupt:
        print("已取消", file=sys.stderr)
        return 130
    except Exception:  # pragma: no cover - unexpected bug, keep a traceback
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
