"""AppContext + Services: the composed dependency graph for one invocation."""

from __future__ import annotations

from dataclasses import dataclass, replace

from orzmc.core.mojang import Mojang
from orzmc.domain.options import RuntimeOptions
from orzmc.domain.paths import DEFAULT_ROOT, PathLayout
from orzmc.domain.types import GameType
from orzmc.infra.fs import FileStore
from orzmc.infra.http import HttpClient
from orzmc.infra.log import NullReporter, Reporter
from orzmc.infra.progress import NullProgress, ProgressSink
from orzmc.infra.runner import CommandRunner, ProcessRunner
from orzmc.services.downloader import Downloader
from orzmc.services.java import JavaEnv


@dataclass(frozen=True)
class AppContext:
    """The bound value objects for one launch/deploy operation."""

    options: RuntimeOptions
    paths: PathLayout

    @classmethod
    def build(cls, options: RuntimeOptions) -> AppContext:
        paths = PathLayout(
            root=options.root_dir or DEFAULT_ROOT,
            version=options.version,
            game_type=options.game_type,
        )
        return cls(options=options, paths=paths)

    @property
    def game_type(self) -> GameType:
        return self.options.game_type_obj


class Services:
    """Everything a service needs, wired for one (version-bound) invocation."""

    def __init__(
        self,
        options: RuntimeOptions,
        reporter: Reporter | None = None,
        sink: ProgressSink | None = None,
        http: HttpClient | None = None,
        fs: FileStore | None = None,
    ) -> None:
        self.options = options
        self.reporter = reporter or NullReporter()
        self.sink = sink or NullProgress()
        self.http = http or HttpClient()
        self.fs = fs or FileStore()
        self.cmd = CommandRunner(self.reporter)
        self.process = ProcessRunner(self.reporter)
        self.context = AppContext.build(options)
        self.mojang = Mojang(self.http, self.fs, self.context.paths.version_manifest_path())
        self.downloader = Downloader(self.http, self.fs, self.reporter, self.sink, self.mojang, self.context.paths)
        self.java_env = JavaEnv(self.http, self.fs, self.reporter, self.sink, self.context.paths)

    def for_version(self, version: str) -> Services:
        """A copy of the services bound to a concrete Minecraft version."""
        return Services(
            replace(self.options, version=version),
            reporter=self.reporter,
            sink=self.sink,
            http=self.http,
            fs=self.fs,
        )
