"""Locate the Forge installer URL for a Minecraft version."""

from __future__ import annotations

from urllib.parse import parse_qs, urlparse

from bs4 import BeautifulSoup

from orzmc.infra.http import HttpClient

INDEX_BASE = "https://files.minecraftforge.net/maven/net/minecraftforge/forge"
MAVEN_BASE = "https://maven.minecraftforge.net/net/minecraftforge/forge"


class Forge:
    """Discover the latest Forge installer for a MC version (v2 page)."""

    def __init__(self, http: HttpClient, version: str) -> None:
        self._http = http
        self.version = version
        self.forge_installer_url: str | None = None
        self.full_version: str | None = None

    def discover(self) -> None:
        """Populate ``forge_installer_url`` / ``full_version``; raise when unsupported."""
        page = f"{INDEX_BASE}/index_{self.version}.html"
        html = self._http.get_text(page)
        soup = BeautifulSoup(html, "html.parser")
        for node in soup.select(".classifier-installer"):
            parent = node.parent
            if parent is None:
                continue
            href = str(parent.get("href") or "")
            params = parse_qs(urlparse(href).query)
            full_version = (params.get("full") or [""])[0]
            filename = (params.get("filename") or [""])[0]
            if full_version and filename:
                self.full_version = full_version
                self.forge_installer_url = f"{MAVEN_BASE}/{full_version}/{filename}"
                return
        raise RuntimeError(f"未找到 Minecraft {self.version} 的 Forge 安装器,该版本可能不支持 Forge")
