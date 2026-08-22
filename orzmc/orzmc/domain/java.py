"""Java runtime requirements & version parsing (pure functions)."""

from __future__ import annotations

import re

# Fallback when a version JSON carries no javaVersion metadata.
DEFAULT_JAVA_MAJOR = 8

_VERSION_RE = re.compile(r'version\s+"([0-9][0-9._]*)')


def parse_java_major(output: str) -> int | None:
    """Parse the major version number from `java -version` output.

    Handles both modern (``openjdk version "17.0.8"``) and legacy
    (``java version "1.8.0_202"``) formats. Returns ``None`` when no version
    could be parsed.
    """
    match = _VERSION_RE.search(output)
    if not match:
        return None
    raw = match.group(1)
    parts = raw.split(".")
    if parts and parts[0] == "1":  # 1.8.0_202 → 8
        return int(parts[1]) if len(parts) > 1 else 8
    try:
        return int(parts[0])
    except (ValueError, TypeError):
        return None


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
