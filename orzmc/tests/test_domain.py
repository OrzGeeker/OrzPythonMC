"""Pure domain logic: types, options, paths, java, libraries, launch args, plan."""

from __future__ import annotations

import os

import pytest

from orzmc import (
    DEFAULT_JAVA_MAJOR,
    GameType,
    PathLayout,
    Plan,
    RuntimeOptions,
    Step,
    build_launch_command,
    game_args,
    jvm_args,
    parse_java_major,
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
        assert GameType.VANILLA.is_client_capable
        assert GameType.FORGE.is_client_capable
        assert not GameType.PAPER.is_client_capable
        assert not GameType.SPIGOT.is_client_capable
        assert all(t.is_server_capable for t in GameType)

    def test_needs_jdk_only_for_spigot(self) -> None:
        assert GameType.SPIGOT.needs_jdk
        assert not GameType.VANILLA.needs_jdk
        assert not GameType.FORGE.needs_jdk

    def test_server_jar_name(self) -> None:
        assert GameType.VANILLA.server_jar_name("1.20.4") == "server.jar"
        assert GameType.PAPER.server_jar_name("1.20.4") == "paper-1.20.4.jar"
        assert GameType.SPIGOT.server_jar_name("1.20.4") == "spigot-1.20.4.jar"
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
            layout.client_json_path(),
            layout.client_profiles_dir(),
            layout.client_profile_path("optifine:1.20.4"),
            layout.client_launcher_profiles_path(),
            layout.server_dir(),
            layout.server_build_dir(),
            layout.server_jar_path(),
            layout.server_eula_path(),
            layout.server_properties_path(),
            layout.server_commands_path(),
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
    def test_parse_java_major_modern(self) -> None:
        assert parse_java_major('openjdk version "17.0.8" 2023-07-18') == 17
        assert parse_java_major('openjdk version "21.0.1" 2023-10-17') == 21

    def test_parse_java_major_legacy(self) -> None:
        assert parse_java_major('java version "1.8.0_202"') == 8
        assert parse_java_major('openjdk version "1.8.0_392"') == 8

    def test_parse_java_major_garbage(self) -> None:
        assert parse_java_major("not a java output") is None

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


# ── plan ────────────────────────────────────────────────────────────────────


class TestPlan:
    def test_steps_chain(self) -> None:
        plan = Plan([Step("a", lambda ctx: {"value": 1}), Step("b", lambda ctx: {"value": ctx["value"] + 1})])
        assert plan.run()["value"] == 2

    def test_ctx_injected(self) -> None:
        plan = Plan([Step("inc", lambda ctx: {"value": ctx.get("value", 0) + 1})])
        assert plan.run({"value": 10})["value"] == 11
