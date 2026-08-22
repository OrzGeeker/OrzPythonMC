"""Mojang version manifest & asset API adapter.

The manifest cache directory is injected by the caller — no hidden global state.
"""

from __future__ import annotations

from typing import Any

from orzmc.infra.fs import FileStore
from orzmc.infra.http import HttpClient

VERSION_MANIFEST_URL = "https://launchermeta.mojang.com/mc/game/version_manifest.json"
ASSET_BASE_URL = "https://resources.download.minecraft.net/"


class Mojang:
    def __init__(self, http: HttpClient, fs: FileStore, manifest_path: str) -> None:
        self._http = http
        self._fs = fs
        self._manifest_path = manifest_path

    def load_manifest(self, update: bool = False) -> dict[str, Any]:
        """Return the version manifest; refresh it when ``update`` or not cached."""
        if not update and self._fs.is_file(self._manifest_path):
            return self._fs.read_json(self._manifest_path)
        try:
            data = self._http.get_json(VERSION_MANIFEST_URL)
        except Exception as exc:
            raise RuntimeError("无法获取 Minecraft 版本清单(请检查网络连接)") from exc
        self._fs.write_json(self._manifest_path, data)
        return data

    def release_version_ids(self, update: bool = False) -> list[str]:
        manifest = self.load_manifest(update)
        return [v["id"] for v in manifest.get("versions", []) if v.get("type") == "release"]

    def latest_release_id(self) -> str:
        ids = self.release_version_ids()
        return ids[0] if ids else ""

    def version_info(self, version_id: str) -> dict[str, Any] | None:
        manifest = self.load_manifest()
        for v in manifest.get("versions", []):
            if v.get("id") == version_id:
                return v
        return None

    def version_json_url_and_sha1(self, version_id: str) -> tuple[str, str] | None:
        """(url of <version>.json, its sha1). The sha1 is the manifest's ``sha1`` field."""
        info = self.version_info(version_id)
        if not info or not info.get("url"):
            return None
        return info["url"], info.get("sha1", "")

    @staticmethod
    def assets_object_url(sha1: str) -> str:
        return ASSET_BASE_URL + sha1[:2] + "/" + sha1
