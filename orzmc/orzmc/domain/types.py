"""Game types for OrzMC."""

from __future__ import annotations

from enum import Enum


class GameType(str, Enum):
    """A game flavor (client mod or server core type)."""

    VANILLA = "vanilla"
    PAPER = "paper"
    SPIGOT = "spigot"
    FORGE = "forge"

    @property
    def is_client_capable(self) -> bool:
        """Whether this type can be launched as a client."""
        return self in (GameType.VANILLA, GameType.FORGE)

    @property
    def is_server_capable(self) -> bool:
        """Whether this type can be deployed as a server."""
        return self in (GameType.VANILLA, GameType.PAPER, GameType.SPIGOT, GameType.FORGE)

    @property
    def needs_jdk(self) -> bool:
        """Spigot is built from source with BuildTools → needs javac (full JDK)."""
        return self == GameType.SPIGOT

    @classmethod
    def parse(cls, value: str) -> GameType:
        """Parse a type name; raise ValueError on unknown values."""
        return cls(value.strip().lower())

    def server_jar_name(self, version: str) -> str:
        """Canonical server core jar filename for this type."""
        if self == GameType.PAPER:
            return f"paper-{version}.jar"
        if self == GameType.SPIGOT:
            return f"spigot-{version}.jar"
        if self == GameType.FORGE:
            return f"forge-{version}.jar"
        return "server.jar"
