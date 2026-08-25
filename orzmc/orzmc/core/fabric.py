"""Fabric loader resolution & library download (fabric-meta API)."""

from __future__ import annotations

from typing import Any

from orzmc.core.profiles import ProfileAddon
from orzmc.domain.libraries import Library
from orzmc.infra.http import HttpClient

META_BASE = "https://meta.fabricmc.net/v2"


class Fabric:
    def __init__(self, http: HttpClient, version: str, loader: str | None = None) -> None:
        self._http = http
        self.version = version
        self.loader = loader

    def profile(self) -> ProfileAddon:
        """Resolve the fabric-loader profile json for this MC version."""
        loader_version = self.loader or self.latest_loader_version()
        installer_version = self.latest_installer_version()
        url = f"{META_BASE}/versions/loader/{self.version}/{loader_version}/{installer_version}/profile/json"
        config: dict[str, Any] = self._http.get_json(url)

        libraries: list[Library] = []
        for lib in config.get("libraries", []):
            name = lib.get("name")
            if not name:
                continue
            # fabric-meta profile entries carry full download metadata
            url = lib.get("url") or ""
            path = name.replace(":", "/") + ".jar"
            if url:
                # strip the leading path so the jar lands under libraries/
                path = url.replace("https://maven.fabricmc.net/", "").split("?")[0]
            libraries.append(
                Library(
                    name=name,
                    path=path,
                    url=url,
                    sha1=lib.get("sha1"),
                    size=lib.get("size"),
                )
            )

        arguments = config.get("arguments", {})
        jvm_args = [a for a in arguments.get("jvm", []) if isinstance(a, str)]
        game_args = [a for a in arguments.get("game", []) if isinstance(a, str)]
        main_class = _main_class(config)

        return ProfileAddon(libraries=libraries, jvm_args=jvm_args, game_args=game_args, main_class=main_class)

    def latest_loader_version(self) -> str:
        """Latest stable fabric-loader version for this MC version."""
        entries = self._http.get_json(f"{META_BASE}/versions/loader/{self.version}")
        for entry in entries:
            loader = (entry or {}).get("loader", {})
            if loader.get("stable"):
                return loader["version"]
        if entries:
            return entries[0]["loader"]["version"]
        raise RuntimeError(f"Fabric 不支持 Minecraft {self.version}")

    def latest_installer_version(self) -> str:
        """Latest stable fabric-installer version."""
        entries = self._http.get_json(f"{META_BASE}/versions/installer")
        for entry in entries:
            if entry.get("stable"):
                return entry["version"]
        return entries[0]["version"]


def _main_class(config: dict[str, Any]) -> str | None:
    main_class = config.get("mainClass")
    if isinstance(main_class, str):
        return main_class
    if isinstance(main_class, dict):
        return main_class.get("client") or main_class.get("server")
    return None
