"""Backup: zip a server world directory."""

from __future__ import annotations

import os
import zipfile

import pytest
from fakes import FakeReporter

from orzmc import Backup, FileStore


def _seed_world(tmp_path) -> str:
    fs = FileStore()
    root = str(tmp_path)
    world = os.path.join(root, "versions", "1.20.4", "server", "vanilla", "world")
    fs.ensure_dir(os.path.join(world, "region"))
    fs.write_text(os.path.join(world, "level.dat"), "level")
    fs.write_text(os.path.join(world, "region", "r.0.0.mca"), "region-data")
    return root


class TestBackup:
    def test_backup_world(self, tmp_path) -> None:
        root = _seed_world(tmp_path)
        backup = Backup(fs=FileStore(), reporter=FakeReporter(), root_dir=root)
        dest = backup.backup_world("1.20.4", "vanilla")
        assert dest.startswith(os.path.join(root, "backup", "worlds"))
        with zipfile.ZipFile(dest) as zf:
            names = zf.namelist()
        assert "level.dat" in names
        assert "region/r.0.0.mca" in names

    def test_backup_missing_world_raises(self, tmp_path) -> None:
        backup = Backup(fs=FileStore(), root_dir=str(tmp_path))
        with pytest.raises(RuntimeError):
            backup.backup_world("1.20.4", "vanilla")
