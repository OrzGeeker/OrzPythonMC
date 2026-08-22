"""World backup: zip a server's world directory."""

from __future__ import annotations

import os
import zipfile
from datetime import datetime

from orzmc.domain.paths import DEFAULT_ROOT
from orzmc.infra.fs import FileStore
from orzmc.infra.log import NullReporter, Reporter


class Backup:
    def __init__(
        self, fs: FileStore | None = None, reporter: Reporter | None = None, root_dir: str | None = None
    ) -> None:
        self._fs = fs or FileStore()
        self._reporter = reporter or NullReporter()
        self._root = root_dir or DEFAULT_ROOT

    def backup_world(self, version: str, game_type: str = "vanilla") -> str:
        """Zip ``versions/<version>/server/<game_type>/world`` → ``backup/worlds/``."""
        world = os.path.join(self._root, "versions", version, "server", game_type, "world")
        if not self._fs.is_dir(world):
            raise RuntimeError(f"未找到世界目录: {world}")
        timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
        dest = os.path.join(self._root, "backup", "worlds", f"{version}-{game_type}-{timestamp}.zip")
        self._fs.ensure_dir(os.path.dirname(dest))
        count = 0
        with zipfile.ZipFile(dest, "w", zipfile.ZIP_DEFLATED) as zf:
            for root_dir, _, files in os.walk(world):
                for name in files:
                    full = os.path.join(root_dir, name)
                    rel = os.path.relpath(full, world)
                    zf.write(full, rel)
                    count += 1
        self._reporter.success(f"已备份 {count} 个文件到 {dest}")
        return dest
