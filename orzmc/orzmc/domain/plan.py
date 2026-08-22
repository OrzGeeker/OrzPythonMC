"""Step / Plan: a small reusable execution plan abstraction."""

from __future__ import annotations

from collections.abc import Callable
from typing import Any

StepFn = Callable[[dict[str, Any]], dict[str, Any] | None]


class Step:
    """One named step that mutates a shared context dict."""

    def __init__(self, name: str, fn: StepFn) -> None:
        self.name = name
        self.fn = fn

    def run(self, ctx: dict[str, Any]) -> dict[str, Any]:
        result = self.fn(ctx)
        return result or {}


class Plan:
    """Run steps in order, each receiving the accumulated context."""

    def __init__(self, steps: list[Step]) -> None:
        self.steps = steps

    def run(self, ctx: dict[str, Any] | None = None) -> dict[str, Any]:
        context: dict[str, Any] = dict(ctx or {})
        for step in self.steps:
            context.update(step.run(context))
        return context
