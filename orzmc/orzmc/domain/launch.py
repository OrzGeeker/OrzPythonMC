"""Pure assembly of the client launch command (no IO, fully testable)."""

from __future__ import annotations

import os
import shlex

from orzmc.domain.options import RuntimeOptions
from orzmc.domain.paths import PathLayout

DEFAULT_MAIN_CLASS = "net.minecraft.client.main.Main"
LAUNCHER_BRAND = "orzmc"
LAUNCHER_VERSION = "2.0.0"


def jvm_args(version_json: dict, natives_dir: str) -> list[str]:
    """JVM flags from the version JSON (modern ``arguments.jvm`` or legacy template)."""
    if "arguments" in version_json:
        raw = [a for a in version_json["arguments"].get("jvm", []) if isinstance(a, str)]
    else:
        raw = ["-Djava.library.path=${natives_directory}", "-cp", "${classpath}"]
    result: list[str] = []
    for i, arg in enumerate(raw):
        if "${classpath}" in arg:
            continue  # the real classpath is appended explicitly
        if arg == "-cp" and i + 1 < len(raw) and "${classpath}" in raw[i + 1]:
            continue  # drop the -cp flag that belongs to the ${classpath} pair
        if "${natives_directory}" in arg:
            result.append(arg.replace("${natives_directory}", natives_dir))
        else:
            result.append(arg)
    return result


def game_args(version_json: dict, options: RuntimeOptions, paths: PathLayout) -> list[str]:
    """Game arguments (modern ``arguments.game`` or legacy ``minecraftArguments``)."""
    if "arguments" in version_json:
        args = [a for a in version_json["arguments"].get("game", []) if isinstance(a, str)]
        args += [
            "--username",
            options.username,
            "--version",
            options.version or "",
            "--gameDir",
            paths.client_dir(),
            "--assetsDir",
            paths.client_assets_dir(),
            "--assetIndex",
            str((version_json.get("assetIndex") or {}).get("id", "") or ""),
            "--uuid",
            "",
            "--accessToken",
            "0",
            "--userType",
            "legacy",
        ]
        return args

    template = version_json.get("minecraftArguments", "")
    tokens = {
        "${auth_player_name}": options.username,
        "${version_name}": options.version or "",
        "${game_directory}": paths.client_dir(),
        "${assets_root}": paths.client_assets_dir(),
        "${assets_index_name}": str((version_json.get("assetIndex") or {}).get("id", "") or ""),
        "${auth_uuid}": "",
        "${auth_access_token}": "0",
        "${user_type}": "legacy",
        "${version_type}": "release",
        "${user_properties}": "{}",
        "${resolution_width}": "854",
        "${resolution_height}": "480",
    }
    result = template
    for key, value in tokens.items():
        result = result.replace(key, value)
    return shlex.split(result)


def build_launch_command(
    java_bin: str,
    version_json: dict,
    paths: PathLayout,
    options: RuntimeOptions,
    classpath: list[str],
    main_class: str,
    extra_jvm: list[str] | None = None,
    extra_game: list[str] | None = None,
) -> list[str]:
    """Assemble the full client launch command (pure)."""
    cmd = [java_bin]
    cmd += [f"-Xms{options.min_mem}", f"-Xmx{options.max_mem}"]
    cmd += jvm_args(version_json, paths.client_natives_dir())
    cmd += [f"-Dminecraft.launcher.brand={LAUNCHER_BRAND}", f"-Dminecraft.launcher.version={LAUNCHER_VERSION}"]
    if options.jvm_opts:
        cmd += shlex.split(options.jvm_opts)
    if extra_jvm:
        cmd += extra_jvm
    cmd += ["-cp", os.pathsep.join(classpath)]
    cmd.append(main_class)
    cmd += game_args(version_json, options, paths)
    if extra_game:
        cmd += extra_game
    return cmd
