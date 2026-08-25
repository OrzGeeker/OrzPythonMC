"""Process execution: long-lived streaming processes (java client/server).

Replaces the scattered ``os.system`` / ``os.popen`` calls from the old codebase.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable

from orzmc.infra.log import NullReporter, Reporter


class ProcessRunner:
    """Run long-lived processes (java client/server) with streamed output."""

    def __init__(self, reporter: Reporter | None = None) -> None:
        self._reporter = reporter or NullReporter()

    def run_stream(
        self,
        args: list[str],
        on_line: Callable[[str], None] | None = None,
        cwd: str | None = None,
    ) -> int:
        """Run a foreground process, forwarding its stdout lines to ``on_line``.

        Blocks until the process exits and returns its exit code.
        """
        self._reporter.debug("$ " + " ".join(args))
        proc = subprocess.Popen(
            args,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            cwd=cwd,
        )
        if proc.stdout is not None:
            for line in proc.stdout:
                line = line.rstrip("\n")
                if on_line:
                    on_line(line)
        return proc.wait()

    def run_detached(
        self,
        args: list[str],
        cwd: str | None = None,
        log_path: str | None = None,
    ) -> subprocess.Popen:
        """Launch a process in the background and return its handle.

        ``stdout``/``stderr`` are redirected to ``log_path`` (appended) when
        given, otherwise discarded. The caller keeps the handle so it can poll
        for early exit instead of trusting that a spawned process survives.
        """
        self._reporter.debug("$ (detached) " + " ".join(args))
        flags = 0
        if os.name == "nt":
            flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        if log_path:
            os.makedirs(os.path.dirname(log_path), exist_ok=True)
            # Popen dup()s the handle into the child, so the parent's copy can be
            # closed here while the child keeps writing to the log.
            with open(log_path, "ab") as out:
                return subprocess.Popen(
                    args,
                    cwd=cwd,
                    stdin=subprocess.DEVNULL,
                    stdout=out,
                    stderr=subprocess.STDOUT,
                    start_new_session=os.name != "nt",
                    creationflags=flags,
                )
        return subprocess.Popen(
            args,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=os.name != "nt",
            creationflags=flags,
        )
