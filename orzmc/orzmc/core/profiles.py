"""Shared model for optional client add-ons (OptiFine / Fabric profiles)."""

from __future__ import annotations

from dataclasses import dataclass, field

from orzmc.domain.libraries import Library
from orzmc.infra.fs import FileStore


@dataclass
class ProfileAddon:
    """Result of resolving an optional client add-on.

    ``libraries`` are extra classpath jars; ``jvm_args`` / ``game_args`` are
    appended to the launch command; ``main_class`` overrides the vanilla one.
    """

    libraries: list[Library] = field(default_factory=list)
    jvm_args: list[str] = field(default_factory=list)
    game_args: list[str] = field(default_factory=list)
    main_class: str | None = None


def read_json_if_exists(fs: FileStore, path: str) -> dict | None:
    if not fs.is_file(path):
        return None
    return fs.read_json(path)
