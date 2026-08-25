"""ProgressSink protocol + rich default implementation.

A single shared sink is used for a whole operation: ``start(desc, total)``
reconfigures the current task, ``advance(n)`` moves it forward and ``finish()``
closes it. Callers never touch the rendering details.
"""

from __future__ import annotations

from abc import ABC, abstractmethod


class ProgressSink(ABC):
    """Abstract progress display. The app layer injects its own."""

    @abstractmethod
    def start(self, desc: str, total: int | None = None) -> None: ...

    @abstractmethod
    def advance(self, n: int = 1) -> None: ...

    @abstractmethod
    def finish(self) -> None: ...


class NullProgress(ProgressSink):
    """No-op implementation used in tests and when progress is unwanted."""

    def start(self, desc: str, total: int | None = None) -> None: ...

    def advance(self, n: int = 1) -> None: ...

    def finish(self) -> None: ...


class RichProgress(ProgressSink):
    """Renders one rich progress task; reused across a whole operation."""

    def __init__(self) -> None:
        from rich.progress import BarColumn, Progress, TaskID, TextColumn, TimeElapsedColumn

        self._progress = Progress(
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("{task.completed}"),
            TimeElapsedColumn(),
        )
        self._task_id: TaskID | None = None

    @property
    def is_live(self) -> bool:
        return bool(self._progress.live)

    def _ensure_live(self) -> None:
        if not self._progress.live:
            self._progress.start()

    def start(self, desc: str, total: int | None = None) -> None:
        self._ensure_live()
        if self._task_id is None:
            self._task_id = self._progress.add_task(desc, total=total)
        else:
            self._progress.update(self._task_id, description=desc, total=total, completed=0)

    def advance(self, n: int = 1) -> None:
        if self._task_id is not None:
            self._progress.advance(self._task_id, n)

    def finish(self) -> None:
        if self._task_id is not None:
            self._progress.stop_task(self._task_id)
            self._progress.remove_task(self._task_id)
            self._task_id = None

    def close(self) -> None:
        if self._task_id is not None:
            self.finish()
        if self._progress.live:
            self._progress.stop()
