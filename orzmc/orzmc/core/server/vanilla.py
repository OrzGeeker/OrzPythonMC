"""Vanilla server core: Mojang's official server jar, sha1-verified."""

from __future__ import annotations

from orzmc.core.server.base import CoreProvider, ServerPrepare
from orzmc.domain.types import GameType


class VanillaProvider(CoreProvider):
    game_type = GameType.VANILLA

    def obtain(self, prepare: ServerPrepare) -> None:
        server = prepare.version_json.get("downloads", {}).get("server") or {}
        url = server.get("url")
        if not url:
            raise RuntimeError("该版本没有官方服务端下载")
        prepare.download(
            url,
            prepare.paths.server_jar_path(),
            f"下载服务端 {prepare.version}",
            sha1=server.get("sha1"),
            force=prepare.force_download,
        )


CoreProvider.register(VanillaProvider())
