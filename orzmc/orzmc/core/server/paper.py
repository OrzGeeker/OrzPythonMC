"""Paper server core: resolve the latest Paper build and download it."""

from __future__ import annotations

from orzmc.core.server.base import CoreProvider, ServerPrepare
from orzmc.domain.types import GameType
from orzmc.infra.http import HttpClient

API_BASE = "https://api.papermc.io/v2"


class PaperAPI:
    def __init__(self, http: HttpClient) -> None:
        self._http = http

    def download_url(self, mc_version: str) -> str:
        """Resolve the latest Paper build download URL for ``mc_version``."""
        project = self._http.get_json(f"{API_BASE}/projects/paper")
        versions: list[str] = project.get("versions", [])
        matched = _match_version(versions, mc_version)
        if matched is None:
            raise RuntimeError(f"Paper 不支持 Minecraft {mc_version}")

        build_meta = self._http.get_json(f"{API_BASE}/projects/paper/versions/{matched}")
        builds: list[int] = build_meta.get("builds", [])
        if not builds:
            raise RuntimeError(f"Paper {matched} 没有可用构建")
        build_number = builds[-1]

        build_info = self._http.get_json(f"{API_BASE}/projects/paper/versions/{matched}/builds/{build_number}")
        jar_name = (build_info.get("downloads", {}).get("application", {}) or {}).get("name")
        if not jar_name:
            raise RuntimeError(f"Paper {matched} build {build_number} 没有可下载的 jar")
        return f"{API_BASE}/projects/paper/versions/{matched}/builds/{build_number}/downloads/{jar_name}"


def _match_version(available: list[str], mc_version: str) -> str | None:
    """Return the newest available version for ``mc_version`` (exact or prefixed)."""
    exact: list[str] = []
    prefixed: list[str] = []
    for v in available:
        if v == mc_version:
            exact.append(v)
        elif v.startswith(f"{mc_version}-"):
            prefixed.append(v)
    candidates = exact or prefixed
    if not candidates:
        return None
    # versions are ordered oldest→newest; pick the last
    return candidates[-1]


class PaperProvider(CoreProvider):
    game_type = GameType.PAPER

    def obtain(self, prepare: ServerPrepare) -> None:
        url = PaperAPI(prepare.http).download_url(prepare.version)
        prepare.download(
            url,
            prepare.paths.server_jar_path(),
            f"下载 Paper {prepare.version}",
            force=prepare.force_download,
        )


CoreProvider.register(PaperProvider())
