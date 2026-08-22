"""OrzMC core library.

This module is the **public API contract**. The application layer (orzmc-app)
and any external project should only import from here; internals live under
``domain`` / ``infra`` / ``core`` / ``services``.
"""

from __future__ import annotations

from collections.abc import Callable

from orzmc.domain.java import DEFAULT_JAVA_MAJOR, parse_java_major, required_java_major
from orzmc.domain.launch import DEFAULT_MAIN_CLASS, build_launch_command, game_args, jvm_args
from orzmc.domain.libraries import Library, resolve_libraries
from orzmc.domain.options import RuntimeOptions
from orzmc.domain.paths import DEFAULT_ROOT, PathLayout
from orzmc.domain.plan import Plan, Step
from orzmc.domain.types import GameType
from orzmc.infra.fs import FileStore
from orzmc.infra.log import NullReporter, Reporter, RichReporter
from orzmc.infra.progress import NullProgress, ProgressSink, RichProgress
from orzmc.services.backup import Backup
from orzmc.services.client import ClientService
from orzmc.services.context import AppContext, Services
from orzmc.services.server import ServerService
from orzmc.services.versions import InstalledVersion, VersionManager
from orzmc.version import __version__

__all__ = [
    "DEFAULT_JAVA_MAJOR",
    "DEFAULT_MAIN_CLASS",
    "DEFAULT_ROOT",
    "AppContext",
    "Backup",
    "ClientService",
    "FileStore",
    "GameType",
    "InstalledVersion",
    "Library",
    "NullProgress",
    "NullReporter",
    "PathLayout",
    "Plan",
    "ProgressSink",
    # protocols & impls
    "Reporter",
    "RichProgress",
    "RichReporter",
    # domain
    "RuntimeOptions",
    "ServerService",
    # services
    "Services",
    "Step",
    "VersionManager",
    # versions
    "__version__",
    "backup_world",
    "build_launch_command",
    "deploy_server",
    "game_args",
    "install_java",
    "jvm_args",
    # entry points
    "launch_client",
    "list_versions",
    "parse_java_major",
    "remote_versions",
    "remove_version",
    "required_java_major",
    "resolve_libraries",
]

# ── entry points ─────────────────────────────────────────────────────────────


def launch_client(
    options: RuntimeOptions,
    reporter: Reporter | None = None,
    sink: ProgressSink | None = None,
    confirm_java: Callable[[int, bool], bool] | None = None,
) -> int:
    """Launch the Minecraft client for ``options`` (auto-installs everything).

    ``confirm_java`` (optional) is consulted before installing a Java runtime.
    """
    base = Services(options, reporter=reporter, sink=sink)
    version = options.version or base.mojang.latest_release_id()
    if not version:
        raise RuntimeError("无法确定 Minecraft 版本")
    return ClientService(base.for_version(version)).run(confirm_java=confirm_java)


def deploy_server(
    options: RuntimeOptions,
    reporter: Reporter | None = None,
    sink: ProgressSink | None = None,
    confirm_java: Callable[[int, bool], bool] | None = None,
    confirm_eula: Callable[[], bool] | None = None,
    on_line: Callable[[str], None] | None = None,
) -> int:
    """Deploy and run a server for ``options`` (auto-installs everything).

    ``confirm_eula`` (optional) accepts the Minecraft EULA interactively when
    ``options.yes`` is not set. ``on_line`` receives streamed server output.
    """
    base = Services(options, reporter=reporter, sink=sink)
    version = options.version or base.mojang.latest_release_id()
    if not version:
        raise RuntimeError("无法确定 Minecraft 版本")
    return ServerService(base.for_version(version)).run(
        confirm_java=confirm_java, confirm_eula=confirm_eula, on_line=on_line
    )


def list_versions(root_dir: str | None = None) -> list[InstalledVersion]:
    """Enumerate installed versions (client / server types) under ``root_dir``."""
    return VersionManager(root_dir=root_dir).list_versions()


def remote_versions(root_dir: str | None = None, update: bool = False) -> list[str]:
    """List Mojang release version ids (fetches/caches the manifest, installs nothing)."""
    options = RuntimeOptions(root_dir=root_dir or DEFAULT_ROOT)
    return Services(options).mojang.release_version_ids(update=update)


def remove_version(
    version: str,
    *,
    is_client: bool = True,
    game_type: str | None = None,
    root_dir: str | None = None,
    yes: bool = False,
    reporter: Reporter | None = None,
    confirm: Callable[[str], bool] | None = None,
) -> bool:
    """Remove a version's client or a specific server type. ``confirm`` is
    consulted unless ``yes`` is set."""
    manager = VersionManager(root_dir=root_dir)
    return manager.remove(version, is_client=is_client, game_type=game_type, yes=yes, confirm=confirm)


def backup_world(
    version: str,
    game_type: str = "vanilla",
    root_dir: str | None = None,
    reporter: Reporter | None = None,
) -> str:
    """Back up ``versions/<version>/server/<game_type>/world`` to ``backup/worlds/``."""
    return Backup(reporter=reporter, root_dir=root_dir).backup_world(version, game_type)


def install_java(
    major: int,
    *,
    need_jdk: bool = False,
    root_dir: str | None = None,
    reporter: Reporter | None = None,
    sink: ProgressSink | None = None,
    confirm: Callable[[int, bool], bool] | None = None,
) -> str:
    """Ensure a sandboxed Java ``major`` is installed under ``root_dir/java/``.

    Returns the managed ``bin/java`` path.
    """
    options = RuntimeOptions(root_dir=root_dir or DEFAULT_ROOT)
    return Services(options, reporter=reporter, sink=sink).java_env.resolve(major, need_jdk=need_jdk, confirm=confirm)
