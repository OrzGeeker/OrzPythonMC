"""Process execution: short-lived commands + long-lived streaming processes.

Replaces the scattered ``os.system`` / ``os.popen`` calls from the old codebase.
"""

from __future__ import annotations

import os
import subprocess
from collections.abc import Callable
from dataclasses import dataclass

from orzmc.infra.log import NullReporter, Reporter


@dataclass(frozen=True)
class CommandResult:
    code: int
    stdout: str
    stderr: str


class CommandRunner:
    """Run short-lived commands and capture their output."""

    def __init__(self, reporter: Reporter | None = None) -> None:
        self._reporter = reporter or NullReporter()

    def run(self, cmd: list[str] | str, check: bool = False, cwd: str | None = None) -> CommandResult:
        self._reporter.debug(f"$ {cmd if isinstance(cmd, str) else ' '.join(cmd)}")
        proc = subprocess.run(
            cmd,
            shell=isinstance(cmd, str),
            cwd=cwd,
            capture_output=True,
            text=True,
        )
        if check and proc.returncode != 0:
            raise RuntimeError(f"命令执行失败: {cmd}\n{proc.stderr.strip()}")
        return CommandResult(proc.returncode, proc.stdout, proc.stderr)

    def read(self, cmd: list[str] | str, cwd: str | None = None) -> str:
        return self.run(cmd, cwd=cwd).stdout


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

    def run_detached(self, args: list[str], cwd: str | None = None) -> int:
        """Launch a process in the background and return its pid immediately."""
        self._reporter.debug("$ (detached) " + " ".join(args))
        flags = 0
        if os.name == "nt":
            flags = getattr(subprocess, "DETACHED_PROCESS", 0) | getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
        proc = subprocess.Popen(
            args,
            cwd=cwd,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=os.name != "nt",
            creationflags=flags,
        )
        return proc.pid
