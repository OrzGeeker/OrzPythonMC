"""Vanilla client: no add-on — the plain Mojang launch definition suffices."""

from __future__ import annotations

from orzmc.core.client.base import ClientPrepare, ClientProvider
from orzmc.core.profiles import ProfileAddon
from orzmc.domain.types import GameType


class VanillaProvider(ClientProvider):
    game_type = GameType.VANILLA

    def addon(self, prepare: ClientPrepare) -> ProfileAddon | None:
        return None


ClientProvider.register(VanillaProvider())
