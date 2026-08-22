"""OptiFine profile adapter.

OptiFine is installed by the user into the official launcher layout. We read the
generated profile config (``profiles/<id>/<id>.json``) to extract the OptiFine
jar, JVM tweak args and main class. Returns ``None`` when no OptiFine profile is
installed (the caller then runs vanilla).
"""

from __future__ import annotations

import os
from typing import Any

from orzmc.core.profiles import ProfileAddon, read_json_if_exists
from orzmc.domain.libraries import Library
from orzmc.infra.fs import FileStore


class OptiFine:
    def __init__(
        self,
        fs: FileStore,
        launcher_profiles_path: str,
        profile_configs_dir: str,
        version: str,
    ) -> None:
        self._fs = fs
        self._launcher_profiles_path = launcher_profiles_path
        self._profile_configs_dir = profile_configs_dir
        self._version = version

    def _optifine_profile_id(self) -> str | None:
        launcher = read_json_if_exists(self._fs, self._launcher_profiles_path)
        if not launcher:
            return None
        profiles: dict[str, Any] = launcher.get("profiles", {})
        selected = launcher.get("selectedProfile")
        if selected and selected in profiles and "optifine" in str(profiles[selected].get("lastVersionId", "")).lower():
            return selected
        for pid, prof in profiles.items():
            if "optifine" in str(prof.get("lastVersionId", "")).lower():
                return pid
        return None

    def resolve(self) -> ProfileAddon | None:
        """Return the OptiFine add-on, or None when no OptiFine profile is found."""
        profile_id = self._optifine_profile_id()
        if not profile_id:
            return None
        config = read_json_if_exists(
            self._fs, os.path.join(self._profile_configs_dir, profile_id, f"{profile_id}.json")
        )
        if not config:
            return None

        libraries: list[Library] = []
        jvm_args: list[str] = []
        for lib in config.get("libraries", []):
            name = lib.get("name") if isinstance(lib, dict) else None
            if not name:
                continue
            path = f"{name.replace(':', '/')}.jar"
            url = ""
            libraries.append(Library(name=name, path=path, url=url, is_native=False))
        jvm_args = [a for a in config.get("arguments", {}).get("jvm", []) if isinstance(a, str)]
        return ProfileAddon(
            libraries=libraries,
            jvm_args=jvm_args,
            main_class=config.get("mainClass"),
        )
