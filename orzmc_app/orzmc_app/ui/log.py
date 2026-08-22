"""Textual reporter: bridge library ``Reporter`` output into a RichLog widget.

The library emits semantic log lines through the ``Reporter`` protocol; the TUI
injects this implementation, which hops every line onto the Textual event loop
(worker threads → main thread) and renders it with a per-level style.
"""

from __future__ import annotations

from collections.abc import Callable

from orzmc.infra.log import Reporter

_LEVEL_STYLE = {
    "debug": "dim",
    "info": "cyan",
    "warn": "yellow",
    "error": "bold red",
    "success": "green",
    "plain": "",
    "server": "bold",
}


class TuiReporter(Reporter):
    """Forwards every log line to ``write(text, style)`` (thread-safe caller)."""

    def __init__(self, write: Callable[[str, str], None]) -> None:
        self._write = write

    def _emit(self, level: str, text: str) -> None:
        self._write(text, _LEVEL_STYLE.get(level, ""))

    def debug(self, text: str) -> None:
        self._emit("debug", text)

    def info(self, text: str) -> None:
        self._emit("info", text)

    def warn(self, text: str) -> None:
        self._emit("warn", text)

    def error(self, text: str) -> None:
        self._emit("error", text)

    def success(self, text: str) -> None:
        self._emit("success", text)

    def plain(self, text: str) -> None:
        self._emit("plain", text)
