"""Textual progress sink: drives a ProgressBar from worker threads.

One sink instance is reused for a whole operation: ``start`` reconfigures the
current task, ``advance`` moves it forward and ``finish`` completes it. Every
call hops onto the Textual event loop via the injected callback.
"""

from __future__ import annotations

from collections.abc import Callable

from orzmc.infra.progress import ProgressSink

# update(desc, total, advance): desc+total = new task, advance = increment,
# (None, None, None) = finish.
ProgressUpdate = Callable[[str | None, int | None, int | None], None]


class TuiProgressSink(ProgressSink):
    def __init__(self, update: ProgressUpdate) -> None:
        self._update = update

    def start(self, desc: str, total: int | None = None) -> None:
        self._update(desc, total, 0)

    def advance(self, n: int = 1) -> None:
        self._update(None, None, n)

    def finish(self) -> None:
        self._update(None, None, None)
