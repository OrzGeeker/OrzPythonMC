"""Pure domain logic: types, options, paths, java, libraries, launch args."""

from __future__ import annotations

import os

import pytest

from orzmc import (
    DEFAULT_JAVA_MAJOR,
    GameType,
    PathLayout,
    RuntimeOptions,
    build_launch_command,
    game_args,
    jvm_args,
    required_java_major,
    resolve_libraries,
)

# ── GameType ────────────────────────────────────────────────────────────────


class TestGameType:
    def test_parse(self) -> None:
        assert GameType.parse("vanilla") == GameType.VANILLA
        assert GameType.parse("PAPER") == GameType.PAPER
        with pytest.raises(ValueError):
            GameType.parse("bogus")

    def test_capabilities(self) -> None:
        # Client types: vanilla / fabric / forge (each pairs with its server).
        assert GameType.VANILLA.is_client_capable
        assert GameType.FABRIC.is_client_capable
        assert GameType.FORGE.is_client_capable
        assert not GameType.PAPER.is_client_capable  # paper is server-only
        assert all(t.is_server_capable for t in GameType)

    def test_server_jar_name(self) -> None:
        assert GameType.VANILLA.server_jar_name("1.20.4") == "server.jar"
        assert GameType.PAPER.server_jar_name("1.20.4") == "paper-1.20.4.jar"
        assert GameType.FABRIC.server_jar_name("1.20.4") == "fabric-server-launch.jar"
        assert GameType.FORGE.server_jar_name("1.20.4") == "forge-1.20.4.jar"


# ── RuntimeOptions ──────────────────────────────────────────────────────────


class TestRuntimeOptions:
    def test_defaults(self) -> None:
        opts = RuntimeOptions()
        assert opts.is_client
        assert opts.username == "guest"
        assert opts.game_type == "vanilla"
        assert opts.min_mem == "512M"
        assert opts.max_mem == "2G"
        assert opts.game_type_obj == GameType.VANILLA

    def test_frozen(self) -> None:
        opts = RuntimeOptions(version="1.20.4")
        with pytest.raises(AttributeError):
            opts.version = "1.21"  # type: ignore[misc]


# ── PathLayout ──────────────────────────────────────────────────────────────


class TestPathLayout:
    def test_purity_getters_create_no_dirs(self, tmp_path) -> None:
        root = str(tmp_path / "minecraft")
        layout = PathLayout(root=root, version="1.20.4", game_type="paper")
        # touch every getter
        _ = [
            layout.versions_dir(),
            layout.version_dir(),
            layout.java_dir(),
            layout.java_major_dir(17),
            layout.java_bin(17),
            layout.cache_dir(),
            layout.version_manifest_path(),
            layout.download_tmp_dir(),
            layout.backup_dir(),
            layout.worlds_backup_dir(),
            layout.music_dir("1.20.4"),
            layout.client_dir(),
            layout.client_assets_dir(),
            layout.client_indexes_dir(),
            layout.client_objects_dir(),
            layout.client_object_path("abc123"),
            layout.client_libraries_dir(),
            layout.client_library_path("net/minecraft/1.20.4/mc.jar"),
            layout.client_natives_dir(),
            layout.client_jar_path(),
            layout.client_profiles_dir(),
            layout.client_profile_path("1.20.4"),
            layout.client_launcher_profiles_path(),
            layout.server_dir(),
            layout.server_build_dir(),
            layout.server_jar_path(),
            layout.server_eula_path(),
            layout.server_properties_path(),
            layout.server_plugins_dir(),
            layout.server_world_dir(),
        ]
        assert not os.path.exists(root)

    def test_layout_shape(self) -> None:
        layout = PathLayout(root="/base", version="1.20.4", game_type="vanilla")
        assert layout.versions_dir() == "/base/versions"
        assert layout.version_dir() == "/base/versions/1.20.4"
        assert layout.client_dir() == "/base/versions/1.20.4/client"
        assert layout.server_dir() == "/base/versions/1.20.4/server/vanilla"
        assert layout.java_major_dir(8) == "/base/java/8"
        assert layout.java_bin(17) == os.path.join("/base/java/17/bin", "java")
        assert layout.server_jar_path() == "/base/versions/1.20.4/server/vanilla/server.jar"
        assert layout.client_object_path("abcd") == "/base/versions/1.20.4/client/assets/objects/ab/abcd"


# ── domain/java ─────────────────────────────────────────────────────────────


class TestJava:
    def test_required_java_major_reads_metadata(self) -> None:
        assert required_java_major({"javaVersion": {"majorVersion": 17}}) == 17
        assert required_java_major({"javaVersion": {"majorVersion": "21"}}) == 21

    def test_required_java_major_defaults_to_8(self) -> None:
        assert required_java_major({}) == DEFAULT_JAVA_MAJOR
        assert required_java_major(None) == DEFAULT_JAVA_MAJOR
        assert required_java_major({"javaVersion": {}}) == DEFAULT_JAVA_MAJOR


# ── libraries ───────────────────────────────────────────────────────────────

SAMPLE_VERSION_JSON = {
    "libraries": [
        {
            "name": "com.example:lib1:1.0",
            "downloads": {
                "artifact": {
                    "path": "com/example/lib1/1.0/lib1-1.0.jar",
                    "url": "https://libraries.minecraft.net/com/example/lib1/1.0/lib1-1.0.jar",
                    "sha1": "abc",
                    "size": 100,
                }
            },
        },
        {
            "name": "org.lwjgl:lwjgl:3.3.1",
            "natives": {"linux": "natives-linux", "osx": "natives-osx", "windows": "natives-windows"},
            "downloads": {
                "classifiers": {
                    "natives-linux": {
                        "path": "org/lwjgl/lwjgl/3.3.1/lwjgl-3.3.1-natives-linux.jar",
                        "url": "https://libraries.minecraft.net/org/lwjgl/lwjgl/3.3.1/lwjgl-3.3.1-natives-linux.jar",
                    }
                }
            },
        },
        {
            "name": "com.only.mac:thing:1.0",
            "rules": [{"action": "disallow", "os": {"name": "osx"}}],
            "downloads": {
                "artifact": {
                    "path": "com/only/mac/thing/1.0/thing-1.0.jar",
                    "url": "https://libraries.minecraft.net/com/only/mac/thing/1.0/thing-1.0.jar",
                }
            },
        },
        # Modern native layout (1.20.4+): classifier embedded in the coordinates,
        # an OS-restricting rules list, and downloads.artifact = the classifier jar.
        {
            "name": "org.lwjgl:lwjgl-glfw:3.3.2:natives-linux",
            "rules": [{"action": "allow", "os": {"name": "linux"}}],
            "downloads": {
                "artifact": {
                    "path": "org/lwjgl/lwjgl-glfw/3.3.2/lwjgl-glfw-3.3.2-natives-linux.jar",
                    "url": "https://libraries.minecraft.net/org/lwjgl/lwjgl-glfw/3.3.2/lwjgl-glfw-3.3.2-natives-linux.jar",
                    "sha1": "def",
                    "size": 115553,
                }
            },
        },
        {
            "name": "com.fallback:no-downloads:1.0",
        },
    ]
}


class TestLibraries:
    def test_linux(self) -> None:
        libs = resolve_libraries(SAMPLE_VERSION_JSON, os_name="linux")
        names = {lib.name for lib in libs}
        assert "com.example:lib1:1.0" in names
        # disallow-only rule: no allow rule ever matches → excluded (launcher semantics)
        assert "com.only.mac:thing:1.0" not in names
        assert "com.fallback:no-downloads:1.0" in names  # maven URL fallback
        native = next(lib for lib in libs if lib.is_native)
        assert native.path.endswith("lwjgl-3.3.1-natives-linux.jar")

    def test_osx_excludes_disallowed(self) -> None:
        libs = resolve_libraries(SAMPLE_VERSION_JSON, os_name="osx")
        names = {lib.name for lib in libs}
        assert "com.only.mac:thing:1.0" not in names
        native = next(lib for lib in libs if lib.is_native)
        assert native.path.endswith("natives-osx.jar")

    def test_modern_natives_classifier_in_name(self) -> None:
        libs = resolve_libraries(SAMPLE_VERSION_JSON, os_name="linux")
        modern = [lib for lib in libs if lib.is_native and "lwjgl-glfw" in lib.name]
        assert len(modern) == 1
        assert modern[0].path.endswith("lwjgl-glfw-3.3.2-natives-linux.jar")
        assert modern[0].url.endswith("lwjgl-glfw-3.3.2-natives-linux.jar")
        assert modern[0].sha1 == "def"

    def test_modern_natives_filtered_to_os(self) -> None:
        libs = resolve_libraries(SAMPLE_VERSION_JSON, os_name="osx")
        names = {lib.name for lib in libs}
        assert "org.lwjgl:lwjgl-glfw:3.3.2:natives-linux" not in names

    def test_fallback_maven_url(self) -> None:
        libs = resolve_libraries(SAMPLE_VERSION_JSON, os_name="linux")
        fallback = next(lib for lib in libs if lib.name == "com.fallback:no-downloads:1.0")
        assert fallback.url == "https://libraries.minecraft.net/com/fallback/no-downloads/1.0/no-downloads-1.0.jar"


# ── launch args ─────────────────────────────────────────────────────────────

LAUNCH_JSON = {
    "arguments": {
        "game": ["--demo"],
        "jvm": ["-Djava.library.path=${natives_directory}", "-XX:+UseG1GC", "-cp", "${classpath}"],
    },
    "mainClass": "net.minecraft.client.main.Main",
    "assetIndex": {"id": "1.20"},
}

# Mirrors the rule-based structure of a real 1.20.4 version JSON.
RULE_LAUNCH_JSON = {
    "arguments": {
        "jvm": [
            {"rules": [{"action": "allow", "os": {"name": "osx"}}], "value": ["-XstartOnFirstThread"]},
            {"rules": [{"action": "allow", "os": {"name": "windows"}}], "value": "-XX:HeapDumpPath=ignored"},
            {"rules": [{"action": "allow", "os": {"arch": "x86"}}], "value": "-Xss1M"},
            "-Djava.library.path=${natives_directory}",
            "-Dminecraft.launcher.brand=${launcher_name}",
            "-Dminecraft.launcher.version=${launcher_version}",
            "-cp",
            "${classpath}",
        ],
        "game": [
            "--username ${auth_player_name}",
            "--version ${version_name}",
            "--gameDir ${game_directory}",
            "--assetsDir ${assets_root}",
            "--assetIndex ${assets_index_name}",
            "--uuid ${auth_uuid}",
            "--accessToken ${auth_access_token}",
            "--clientId ${clientid}",
            "--userType ${user_type}",
            "--versionType ${version_type}",
            {
                "rules": [{"action": "allow", "features": {"has_custom_resolution": True}}],
                "value": ["--width", "${resolution_width}", "--height", "${resolution_height}"],
            },
            {"rules": [{"action": "allow", "features": {"is_demo_user": True}}], "value": "--demo"},
        ],
    },
    "mainClass": "net.minecraft.client.main.Main",
    "assetIndex": {"id": "1.20"},
}


class TestLaunchArgs:
    def test_jvm_args(self) -> None:
        args = jvm_args(LAUNCH_JSON, natives_dir="/natives")
        assert "-Djava.library.path=/natives" in args
        assert "-XX:+UseG1GC" in args
        assert "${classpath}" not in args
        assert "-cp" not in args

    def test_jvm_args_legacy(self) -> None:
        args = jvm_args({"minecraftArguments": "--demo"}, natives_dir="/natives")
        assert "-Djava.library.path=/natives" in args
        assert "-cp" not in args

    def test_game_args(self) -> None:
        options = RuntimeOptions(version="1.20.4", username="tester")
        paths = PathLayout(root="/base", version="1.20.4")
        args = game_args(LAUNCH_JSON, options, paths)
        assert "--demo" in args
        assert args[args.index("--username") + 1] == "tester"
        assert args[args.index("--gameDir") + 1] == "/base/versions/1.20.4/client"

    def test_build_launch_command(self) -> None:
        options = RuntimeOptions(version="1.20.4", username="tester", jvm_opts="-XX:+UseZGC")
        paths = PathLayout(root="/base", version="1.20.4")
        classpath = ["/a.jar", "/b.jar"]
        cmd = build_launch_command(
            "/java/bin/java", LAUNCH_JSON, paths, options, classpath, "net.minecraft.client.main.Main"
        )
        assert cmd[0] == "/java/bin/java"
        assert "-Xms512M" in cmd
        assert "-Xmx2G" in cmd
        assert "-XX:+UseZGC" in cmd
        assert cmd.index("-cp") < cmd.index("net.minecraft.client.main.Main")
        assert os.pathsep.join(classpath) in cmd
        assert "--demo" in cmd

    def test_build_launch_command_extra(self) -> None:
        options = RuntimeOptions(version="1.20.4", username="tester")
        paths = PathLayout(root="/base", version="1.20.4")
        cmd = build_launch_command(
            "/java/bin/java",
            LAUNCH_JSON,
            paths,
            options,
            ["/a.jar"],
            "com.fabricmc.KnotClient",
            extra_jvm=["-Dfabric.skipMcProvider=true"],
            extra_game=["--fabric"],
        )
        assert "-Dfabric.skipMcProvider=true" in cmd
        assert "--fabric" in cmd
        assert "com.fabricmc.KnotClient" in cmd

    def test_jvm_args_rule_based_osx_includes_xstart(self) -> None:
        args = jvm_args(RULE_LAUNCH_JSON, natives_dir="/natives", os_name="osx", arch="x86_64")
        assert "-XstartOnFirstThread" in args
        assert "-XX:HeapDumpPath=ignored" not in args  # windows-only rule
        assert "-Xss1M" not in args  # x86-only rule
        assert "-Djava.library.path=/natives" in args
        assert "-Dminecraft.launcher.brand=orzmc" in args  # ${launcher_name} substituted
        assert "${" not in " ".join(args)

    def test_jvm_args_rule_based_linux_excludes_xstart(self) -> None:
        args = jvm_args(RULE_LAUNCH_JSON, natives_dir="/natives", os_name="linux", arch="x86_64")
        assert "-XstartOnFirstThread" not in args
        assert "-Xss1M" not in args

    def test_jvm_args_rule_based_x86(self) -> None:
        args = jvm_args(RULE_LAUNCH_JSON, natives_dir="/natives", os_name="linux", arch="x86")
        assert "-Xss1M" in args

    def test_game_args_token_substitution_and_rules(self) -> None:
        options = RuntimeOptions(version="1.20.4", username="tester")
        paths = PathLayout(root="/base", version="1.20.4")
        args = game_args(RULE_LAUNCH_JSON, options, paths)
        assert "${" not in " ".join(args)
        assert args[args.index("--username") + 1] == "tester"
        assert args[args.index("--version") + 1] == "1.20.4"
        assert args[args.index("--gameDir") + 1] == "/base/versions/1.20.4/client"
        assert args[args.index("--assetIndex") + 1] == "1.20"
        assert "--width" not in args  # has_custom_resolution defaults false
        assert "--demo" not in args  # is_demo_user defaults false

    def test_game_args_separate_tokens_keep_empty_values(self) -> None:
        # The real 1.20.4 JSON stores "--flag" and "${value}" as separate
        # entries; an empty substituted value (clientId/xuid) must stay so
        # flag/value pairs remain aligned for the game's OptionParser.
        options = RuntimeOptions(version="1.20.4", username="tester")
        paths = PathLayout(root="/base", version="1.20.4")
        json = {
            "arguments": {
                "game": [
                    "--uuid",
                    "${auth_uuid}",
                    "--accessToken",
                    "${auth_access_token}",
                    "--clientId",
                    "${clientid}",
                    "--xuid",
                    "${auth_xuid}",
                    "--userType",
                    "${user_type}",
                ]
            }
        }
        args = game_args(json, options, paths, auth_uuid="00000000-0000-0000-0000-000000000000")
        assert args[args.index("--uuid") + 1] == "00000000-0000-0000-0000-000000000000"
        assert args[args.index("--accessToken") + 1] == "0"
        assert args[args.index("--clientId") + 1] == ""
        assert args[args.index("--xuid") + 1] == ""
        assert args[args.index("--userType") + 1] == "legacy"

    def test_game_args_default_uuid_is_valid(self) -> None:
        # The game calls UUID.fromString on --uuid; the default must be a
        # well-formed random UUID (like the official launcher's offline session).
        import uuid as _uuid

        options = RuntimeOptions(version="1.20.4", username="tester")
        paths = PathLayout(root="/base", version="1.20.4")
        args = game_args(
            {"arguments": {"game": ["--uuid", "${auth_uuid}"]}},
            options,
            paths,
        )
        value = args[args.index("--uuid") + 1]
        assert _uuid.UUID(value).version == 4

    def test_game_args_legacy_template_substitution(self) -> None:
        options = RuntimeOptions(version="1.16.5", username="tester")
        paths = PathLayout(root="/base", version="1.16.5")
        json = {"minecraftArguments": "--username ${auth_player_name} --version ${version_name}"}
        args = game_args(json, options, paths)
        assert args[args.index("--username") + 1] == "tester"
        assert args[args.index("--version") + 1] == "1.16.5"
