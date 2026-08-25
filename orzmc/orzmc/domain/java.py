"""Java runtime requirements & version parsing (pure functions)."""

from __future__ import annotations

# Fallback when a version JSON carries no javaVersion metadata.
DEFAULT_JAVA_MAJOR = 8


def required_java_major(version_json: dict | None) -> int:
    """Java major version required by a Mojang version JSON.

    Reads ``javaVersion.majorVersion`` (default 8 when absent) — the mapping is
    driven by Mojang metadata, never hardcoded per MC version.
    """
    if not version_json:
        return DEFAULT_JAVA_MAJOR
    java_version = version_json.get("javaVersion") or {}
    major = java_version.get("majorVersion")
    if major is not None:
        try:
            return int(major)
        except (TypeError, ValueError):
            return DEFAULT_JAVA_MAJOR
    return DEFAULT_JAVA_MAJOR
