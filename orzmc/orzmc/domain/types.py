"""Game types for OrzMC."""

from __future__ import annotations

from enum import Enum


class GameType(str, Enum):
    """A game flavor (client mod or server core type).

    Every client-capable type pairs with a server type so no deployed server is
    orphaned: vanilla↔vanilla, fabric↔fabric, forge↔forge; paper servers are
    joinable by the vanilla client (paper is a vanilla-compatible core).
    """

    VANILLA = "vanilla"
    FABRIC = "fabric"
    PAPER = "paper"
    FORGE = "forge"

    @property
    def is_client_capable(self) -> bool:
        """Whether this type can be launched as a client."""
        return self in (GameType.VANILLA, GameType.FABRIC, GameType.FORGE)

    @property
    def is_server_capable(self) -> bool:
        """Whether this type can be deployed as a server."""
        return self in (GameType.VANILLA, GameType.FABRIC, GameType.PAPER, GameType.FORGE)

    @classmethod
    def parse(cls, value: str) -> GameType:
        """Parse a type name; raise ValueError on unknown values."""
        return cls(value.strip().lower())

    def server_jar_name(self, version: str) -> str:
        """Canonical server core jar filename for this type."""
        if self == GameType.PAPER:
            return f"paper-{version}.jar"
        if self == GameType.FORGE:
            return f"forge-{version}.jar"
        if self == GameType.FABRIC:
            return "fabric-server-launch.jar"
        return "server.jar"
