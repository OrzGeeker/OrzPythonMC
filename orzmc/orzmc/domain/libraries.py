"""Resolve the library list (with natives) from a Mojang version JSON."""

from __future__ import annotations

import platform
from dataclasses import dataclass

MAVEN_BASE = "https://libraries.minecraft.net/"


def os_key() -> str:
    """Mojang OS key: 'windows' | 'osx' | 'linux'."""
    system = platform.system().lower()
    return "osx" if system == "darwin" else system


def os_arch() -> str:
    arch = platform.machine().lower()
    if arch in ("aarch64", "arm64"):
        return "arm64"
    if arch in ("x86_64", "amd64"):
        return "x86_64"
    return arch or "x86_64"


@dataclass(frozen=True)
class Library:
    """One resolved library artifact to download into the client libraries dir."""

    name: str
    path: str  # relative path under libraries/
    url: str
    sha1: str | None = None
    size: int | None = None
    is_native: bool = False


def rules_allow(
    rules: list[dict] | None,
    os_name: str,
    os_arch: str,
    features: dict | None = None,
) -> bool:
    """Mojang rules — same semantics as the official launcher.

    Used for both library rules and ``arguments`` rule entries. A rule-less item
    is always allowed. With rules, the last rule that matches the current
    OS/arch/features decides the outcome; when no rule matches the item is
    excluded. This keeps ``{allow, os: linux}`` natives off macOS while honouring
    ``{allow, os: linux}, {disallow, os: osx}`` pairs, and lets game args like
    ``{rules: [{features: {has_custom_resolution: true}}], value: --width}``
    resolve against the current feature set.
    """
    if not rules:
        return True
    features = features or {}
    allowed = False
    for rule in rules:
        action = rule.get("action", "allow")
        os_rule = rule.get("os") or {}
        name = os_rule.get("name")
        arch = os_rule.get("arch")
        matched = True
        if name and name != os_name:
            matched = False
        if arch and arch != os_arch:
            matched = False
        for feature, required in (rule.get("features") or {}).items():
            if bool(features.get(feature)) != bool(required):
                matched = False
        if matched:
            allowed = action == "allow"
    return allowed


def _split_coordinates(coords: str) -> tuple[str, str, str, str | None]:
    parts = coords.split(":")
    group, artifact = parts[0], parts[1]
    version = parts[2] if len(parts) > 2 else "unknown"
    classifier = parts[3] if len(parts) > 3 else None
    return group, artifact, version, classifier


def _artifact_path(coords: str, classifier: str | None = None) -> str:
    group, artifact, version, default_classifier = _split_coordinates(coords)
    classifier = classifier or default_classifier
    filename = f"{artifact}-{version}"
    if classifier:
        filename += f"-{classifier}"
    filename += ".jar"
    return f"{group.replace('.', '/')}/{artifact}/{version}/{filename}"


def resolve_libraries(
    version_json: dict,
    os_name: str | None = None,
    arch: str | None = None,
) -> list[Library]:
    """Resolve the full library list (including OS natives) for a version JSON.

    Pure function — no network or filesystem access.
    """
    os_name = os_name or os_key()
    arch = arch or os_arch()
    libraries: list[Library] = []
    for lib in version_json.get("libraries", []):
        if not rules_allow(lib.get("rules"), os_name, arch):
            continue
        coords = lib.get("name")
        if not coords:
            continue
        downloads = lib.get("downloads") or {}
        classifier: str | None = None
        entry: dict | None = None
        natives = lib.get("natives") or {}
        if natives:
            # Legacy layout: natives dict + downloads.classifiers, e.g.
            # {"linux": "natives-linux"} → classifiers["natives-linux"].
            classifier = natives.get(os_name)
            if not classifier:
                continue
            entry = downloads.get("classifiers", {}).get(classifier)
            is_native = True
        else:
            # Modern layout (1.20.4+): the native classifier is embedded in the
            # coordinates (org.lwjgl:lwjgl-glfw:3.3.2:natives-linux) with an
            # OS-restricting rules list and downloads.artifact = the classifier jar.
            entry = downloads.get("artifact")
            name_classifier = _split_coordinates(coords)[3]
            is_native = bool(name_classifier and name_classifier.startswith("natives-"))

        if entry:
            path = entry.get("path")
            url = entry.get("url")
            if not path or not url:
                continue
            libraries.append(
                Library(
                    name=coords,
                    path=path,
                    url=url,
                    sha1=entry.get("sha1"),
                    size=entry.get("size"),
                    is_native=is_native,
                )
            )
        else:
            path = _artifact_path(coords, classifier)
            libraries.append(
                Library(
                    name=coords,
                    path=path,
                    url=MAVEN_BASE + path,
                    is_native=is_native,
                )
            )
    return libraries
