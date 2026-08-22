"""Client launch use case: prepare files, assemble args, launch."""

from __future__ import annotations

import os
import shutil
import zipfile
from collections.abc import Callable

from orzmc.core.fabric import Fabric
from orzmc.core.optifine import OptiFine
from orzmc.core.profiles import ProfileAddon
from orzmc.domain.java import required_java_major
from orzmc.domain.launch import DEFAULT_MAIN_CLASS, build_launch_command
from orzmc.domain.libraries import resolve_libraries
from orzmc.services.context import Services


class ClientService:
    def __init__(self, services: Services) -> None:
        self._services = services
        self._http = services.http
        self._fs = services.fs
        self._reporter = services.reporter
        self._paths = services.context.paths
        self._options = services.options

    def run(
        self,
        confirm_java: Callable[[int, bool], bool] | None = None,
        on_line: Callable[[str], None] | None = None,
    ) -> int:
        version = self._options.version or ""
        self._reporter.info(f"客户端 {version} ({self._options.game_type})")
        downloader = self._services.downloader

        version_json = downloader.fetch_version_json(version, is_client=True)
        major = required_java_major(version_json)
        java_bin = self._services.java_env.resolve(major, need_jdk=False, confirm=confirm_java)

        downloader.prepare_client(version_json)

        if self._options.extract_music:
            return self._extract_music()

        downloader.write_launcher_profiles(version, self._options.username)

        addon = self._resolve_addon()
        classpath = self._build_classpath(version_json, addon)
        main_class = (addon.main_class if addon else None) or version_json.get("mainClass") or DEFAULT_MAIN_CLASS
        cmd = build_launch_command(
            java_bin,
            version_json,
            self._paths,
            self._options,
            classpath,
            main_class,
            extra_jvm=addon.jvm_args if addon else None,
            extra_game=addon.game_args if addon else None,
        )
        self._reporter.success(f"开始启动客户端 {version}...")
        self._reporter.debug(" ".join(cmd))
        pid = self._services.process.run_detached(cmd, cwd=self._paths.client_dir())
        self._reporter.success(f"客户端已启动 (pid {pid})")
        return 0

    # ── internals ───────────────────────────────────────────────────────────

    def _resolve_addon(self) -> ProfileAddon | None:
        if self._options.optifine:
            addon = OptiFine(
                self._fs,
                self._paths.client_launcher_profiles_path(),
                self._paths.client_profiles_dir(),
                self._options.version or "",
            ).resolve()
            if addon is None:
                self._reporter.warn("未检测到 OptiFine 配置,按原版启动")
            return addon
        if self._options.fabric:
            addon = Fabric(self._http, self._options.version or "").profile()
            downloader = self._services.downloader
            for lib in addon.libraries:
                if lib.url:
                    downloader.download_file(
                        lib.url, self._paths.client_library_path(lib.path), f"下载 {lib.name}", lib.sha1
                    )
            return addon
        return None

    def _build_classpath(self, version_json: dict, addon: ProfileAddon | None) -> list[str]:
        paths = [self._paths.client_jar_path()]
        for lib in resolve_libraries(version_json):
            if not lib.is_native:
                paths.append(self._paths.client_library_path(lib.path))
        if addon:
            for lib in addon.libraries:
                paths.append(self._paths.client_library_path(lib.path))
        return [p for p in paths if self._fs.is_file(p)]

    def _extract_music(self) -> int:
        jar = self._paths.client_jar_path()
        if not self._fs.is_file(jar):
            raise RuntimeError("客户端 jar 不存在,无法提取音乐")
        dest = self._paths.music_dir(self._options.version or "")
        self._fs.ensure_dir(dest)
        count = 0
        with zipfile.ZipFile(jar) as zf:
            for name in zf.namelist():
                if not name.endswith(".ogg"):
                    continue
                target = os.path.join(dest, name.replace("/", os.sep))
                self._fs.ensure_dir(os.path.dirname(target))
                with zf.open(name) as src, open(target, "wb") as out:
                    shutil.copyfileobj(src, out)
                count += 1
        self._reporter.success(f"已提取 {count} 个音乐文件到 {dest}")
        return 0
