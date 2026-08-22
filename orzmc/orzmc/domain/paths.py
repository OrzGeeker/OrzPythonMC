"""Pure path layout for the unified multi-version game root.

All getters are side-effect free: they only build strings, never create
directories. Directory creation happens inside services via ``fs.ensure_dir``.

Layout::

    <root>/
      versions/<mc_version>/
        client/   assets/ libraries/ natives/ profiles/
        server/<server_type>/ ...
      java/<java_major>/
      cache/  backup/
"""

from __future__ import annotations

import os
from dataclasses import dataclass

from orzmc.domain.types import GameType

DEFAULT_ROOT = os.path.join(os.path.expanduser("~"), "minecraft")


def _is_windows() -> bool:
    return os.name == "nt"


@dataclass(frozen=True)
class PathLayout:
    root: str = DEFAULT_ROOT
    version: str | None = None
    game_type: str = GameType.VANILLA.value

    # ── root level ────────────────────────────────────────────────────────

    def versions_dir(self) -> str:
        return os.path.join(self.root, "versions")

    def version_dir(self) -> str:
        return os.path.join(self.versions_dir(), self.version or "")

    def java_dir(self) -> str:
        return os.path.join(self.root, "java")

    def java_major_dir(self, major: int) -> str:
        return os.path.join(self.java_dir(), str(major))

    def java_bin(self, major: int) -> str:
        """Path to the managed java executable (no system java involved)."""
        name = "java.exe" if _is_windows() else "java"
        return os.path.join(self.java_major_dir(major), "bin", name)

    def cache_dir(self) -> str:
        return os.path.join(self.root, "cache")

    def version_manifest_path(self) -> str:
        return os.path.join(self.cache_dir(), "version_manifest.json")

    def download_tmp_dir(self) -> str:
        return os.path.join(self.cache_dir(), "download_tmp")

    def backup_dir(self) -> str:
        return os.path.join(self.root, "backup")

    def worlds_backup_dir(self) -> str:
        return os.path.join(self.backup_dir(), "worlds")

    def music_dir(self, version: str | None = None) -> str:
        base = os.path.join(self.backup_dir(), "music")
        return os.path.join(base, version) if version else base

    # ── client ────────────────────────────────────────────────────────────

    def client_dir(self) -> str:
        return os.path.join(self.version_dir(), "client")

    def client_assets_dir(self) -> str:
        return os.path.join(self.client_dir(), "assets")

    def client_indexes_dir(self) -> str:
        return os.path.join(self.client_assets_dir(), "indexes")

    def client_objects_dir(self) -> str:
        return os.path.join(self.client_assets_dir(), "objects")

    def client_object_path(self, sha1: str) -> str:
        return os.path.join(self.client_objects_dir(), sha1[:2], sha1)

    def client_libraries_dir(self) -> str:
        return os.path.join(self.client_dir(), "libraries")

    def client_library_path(self, rel_path: str) -> str:
        return os.path.join(self.client_libraries_dir(), rel_path)

    def client_natives_dir(self) -> str:
        return os.path.join(self.client_dir(), "natives")

    def client_jar_path(self) -> str:
        return os.path.join(self.client_dir(), f"{self.version}.jar")

    def client_json_path(self) -> str:
        return os.path.join(self.client_dir(), f"{self.version}.json")

    def client_profiles_dir(self) -> str:
        return os.path.join(self.client_dir(), "profiles")

    def client_profile_path(self, profile_id: str) -> str:
        return os.path.join(self.client_profiles_dir(), profile_id, f"{profile_id}.json")

    def client_launcher_profiles_path(self) -> str:
        return os.path.join(self.client_dir(), "launcher_profiles.json")

    # ── server ────────────────────────────────────────────────────────────

    def server_dir(self) -> str:
        return os.path.join(self.version_dir(), "server", self.game_type)

    def server_build_dir(self) -> str:
        return os.path.join(self.server_dir(), "build")

    def server_jar_path(self) -> str:
        name = GameType.parse(self.game_type).server_jar_name(self.version or "")
        return os.path.join(self.server_dir(), name)

    def server_eula_path(self) -> str:
        return os.path.join(self.server_dir(), "eula.txt")

    def server_properties_path(self) -> str:
        return os.path.join(self.server_dir(), "server.properties")

    def server_commands_path(self) -> str:
        return os.path.join(self.server_dir(), "commands.yml")

    def server_plugins_dir(self) -> str:
        return os.path.join(self.server_dir(), "plugins")

    def server_world_dir(self) -> str:
        return os.path.join(self.server_dir(), "world")
