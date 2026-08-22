"""Global cleanup registry + signal handling."""

from __future__ import annotations

import signal
from collections.abc import Callable
from typing import ClassVar


class CleanUp:
    """Register on-exit tasks; runs them on SIGINT/SIGTERM then exits.

    Used for e.g. removing temp files when the process is interrupted.
    """

    _tasks: ClassVar[list[Callable[[], None]]] = []

    @classmethod
    def enable(cls) -> None:
        signal.signal(signal.SIGINT, cls._handler)
        signal.signal(signal.SIGTERM, cls._handler)

    @classmethod
    def register(cls, task: Callable[[], None]) -> None:
        cls._tasks.append(task)

    @classmethod
    def run_all(cls) -> None:
        for task in list(cls._tasks):
            try:
                task()
            except Exception:
                pass
        cls._tasks.clear()

    @classmethod
    def _handler(cls, signum: int, frame: object) -> None:
        cls.run_all()
        raise SystemExit(1)
