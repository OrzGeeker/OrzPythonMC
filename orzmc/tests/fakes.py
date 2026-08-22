"""Shared fakes for library tests: no network, no system java, real tmp dirs.

These live in a normal module (not ``conftest``) so test modules can import
them directly. The tests directory is on ``sys.path`` under pytest's default
``prepend`` import mode, so ``from fakes import ...`` resolves here.
"""

from __future__ import annotations

import os
from typing import NoReturn

from orzmc.infra.http import HttpClient
from orzmc.infra.log import Reporter
from orzmc.infra.progress import ProgressSink


class FakeReporter(Reporter):
    def __init__(self) -> None:
        self.lines: list[tuple[str, str]] = []

    def _add(self, level: str, text: str) -> None:
        self.lines.append((level, text))

    def debug(self, text: str) -> None:
        self._add("debug", text)

    def info(self, text: str) -> None:
        self._add("info", text)

    def warn(self, text: str) -> None:
        self._add("warn", text)

    def error(self, text: str) -> None:
        self._add("error", text)

    def success(self, text: str) -> None:
        self._add("success", text)

    def plain(self, text: str) -> None:
        self._add("plain", text)

    @property
    def texts(self) -> list[str]:
        return [text for _, text in self.lines]


class FakeSink(ProgressSink):
    def __init__(self) -> None:
        self.starts: list[tuple[str, int | None]] = []
        self.advanced = 0

    def start(self, desc: str, total: int | None = None) -> None:
        self.starts.append((desc, total))

    def advance(self, n: int = 1) -> None:
        self.advanced += n

    def finish(self) -> None:
        pass


class FakeHttp(HttpClient):
    """Rejects any real network access; tests seed ``canned_archive``.

    Subclasses ``HttpClient`` (without its session) so mypy treats it as the
    real type; any method added to ``HttpClient`` must be overridden here.
    """

    def __init__(self) -> None:
        self.canned_archive: bytes | None = None
        self.requests: list[tuple[str, str]] = []

    def content_length(self, url: str) -> int | None:
        return None

    def get(self, url: str, params=None, headers=None, stream=False) -> NoReturn:
        raise AssertionError(f"unexpected get: {url}")

    def download(self, url: str, dest_path: str, on_chunk=None) -> int:
        self.requests.append(("download", url))
        if self.canned_archive is None:
            raise AssertionError(f"unexpected download: {url}")
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        with open(dest_path, "wb") as f:
            f.write(self.canned_archive)
        if on_chunk:
            on_chunk(len(self.canned_archive))
        return len(self.canned_archive)

    def get_json(self, url: str, params: dict[str, str] | None = None):
        raise AssertionError(f"unexpected get_json: {url}")

    def get_text(self, url: str, params: dict[str, str] | None = None):
        raise AssertionError(f"unexpected get_text: {url}")
