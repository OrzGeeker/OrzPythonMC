"""Shared model for optional client add-ons (Fabric / Forge profiles)."""

from __future__ import annotations

from dataclasses import dataclass, field

from orzmc.domain.libraries import Library


@dataclass
class ProfileAddon:
    """Result of resolving an optional client add-on.

    ``libraries`` are extra classpath jars; ``jvm_args`` / ``game_args`` are
    appended to the launch command; ``main_class`` overrides the vanilla one.
    """

    libraries: list[Library] = field(default_factory=list)
    jvm_args: list[str] = field(default_factory=list)
    game_args: list[str] = field(default_factory=list)
    main_class: str | None = None
    # Forge ships its own patched game jar: when set, the vanilla client jar is
    # excluded from the classpath so its unpatched classes cannot shadow it.
    uses_own_client_jar: bool = False
