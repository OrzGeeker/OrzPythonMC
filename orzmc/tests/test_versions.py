"""VersionManager: enumerate and remove installed versions."""

from __future__ import annotations

import os

import pytest

from orzmc import FileStore, VersionEntry, VersionManager, remote_version_catalog, remote_versions


def _seed(tmp_path, version: str, client: bool, server_types: list[str]) -> None:
    fs = FileStore()
    root = str(tmp_path)
    if client:
        fs.ensure_dir(os.path.join(root, "versions", version, "client"))
    for st in server_types:
        fs.ensure_dir(os.path.join(root, "versions", version, "server", st))


class TestVersionManager:
    def test_list(self, tmp_path) -> None:
        _seed(tmp_path, "1.20.4", client=True, server_types=["paper"])
        _seed(tmp_path, "1.21", client=False, server_types=["vanilla", "forge"])
        manager = VersionManager(fs=FileStore(), root_dir=str(tmp_path))
        versions = {v.version: v for v in manager.list_versions()}
        assert set(versions) == {"1.20.4", "1.21"}
        assert versions["1.20.4"].has_client
        assert versions["1.20.4"].server_types == ("paper",)
        assert versions["1.21"].server_types == ("forge", "vanilla")
        assert versions["1.21"].describe() == "1.21: server(forge,vanilla)"

    def test_list_empty(self, tmp_path) -> None:
        manager = VersionManager(fs=FileStore(), root_dir=str(tmp_path))
        assert manager.list_versions() == []

    def test_remove_client(self, tmp_path) -> None:
        _seed(tmp_path, "1.20.4", client=True, server_types=["paper"])
        manager = VersionManager(fs=FileStore(), root_dir=str(tmp_path))
        assert manager.remove("1.20.4", is_client=True, yes=True)
        fs = FileStore()
        assert not fs.exists(os.path.join(str(tmp_path), "versions", "1.20.4", "client"))
        # server type remains
        assert fs.is_dir(os.path.join(str(tmp_path), "versions", "1.20.4", "server", "paper"))

    def test_remove_server_type_and_prune_version(self, tmp_path) -> None:
        _seed(tmp_path, "1.20.4", client=True, server_types=["paper"])
        manager = VersionManager(fs=FileStore(), root_dir=str(tmp_path))
        assert manager.remove("1.20.4", is_client=False, game_type="paper", yes=True)
        assert manager.remove("1.20.4", is_client=True, yes=True)
        # both gone → the version dir is pruned entirely
        assert not os.path.exists(os.path.join(str(tmp_path), "versions", "1.20.4"))

    def test_remove_respects_confirm(self, tmp_path) -> None:
        _seed(tmp_path, "1.20.4", client=True, server_types=[])
        manager = VersionManager(fs=FileStore(), root_dir=str(tmp_path))
        removed = manager.remove("1.20.4", is_client=True, yes=False, confirm=lambda desc: False)
        assert not removed
        assert os.path.isdir(os.path.join(str(tmp_path), "versions", "1.20.4", "client"))

    def test_remove_missing_raises(self, tmp_path) -> None:
        manager = VersionManager(fs=FileStore(), root_dir=str(tmp_path))
        with pytest.raises(RuntimeError):
            manager.remove("9.9.9", is_client=True, yes=True)

    def test_remove_server_without_type_raises(self, tmp_path) -> None:
        _seed(tmp_path, "1.20.4", client=True, server_types=["vanilla"])
        manager = VersionManager(fs=FileStore(), root_dir=str(tmp_path))
        with pytest.raises(ValueError):
            manager.remove("1.20.4", is_client=False, yes=True)


class TestRemoteVersions:
    def test_reads_cached_manifest_without_network(self, tmp_path) -> None:
        fs = FileStore()
        root = str(tmp_path)
        manifest = {
            "versions": [
                {"id": "1.21.4", "type": "release"},
                {"id": "1.21.3", "type": "release"},
                {"id": "1.21.2", "type": "snapshot"},
                {"id": "1.20.4", "type": "release"},
            ]
        }
        fs.write_json(
            os.path.join(root, "cache", "version_manifest.json"),
            manifest,
        )
        assert remote_versions(root_dir=root) == ["1.21.4", "1.21.3", "1.20.4"]


class TestRemoteCatalog:
    @staticmethod
    def _seed(tmp_path, manifest: dict) -> str:
        fs = FileStore()
        root = str(tmp_path)
        fs.write_json(os.path.join(root, "cache", "version_manifest.json"), manifest)
        return root

    def test_all_types_in_manifest_order(self, tmp_path) -> None:
        root = self._seed(
            tmp_path,
            {
                "versions": [
                    {"id": "26.2", "type": "release"},
                    {"id": "25w14a", "type": "snapshot"},
                    {"id": "b1.7.3", "type": "old_beta"},
                    {"id": "c0.0.13a", "type": "old_alpha"},
                ]
            },
        )
        assert remote_version_catalog(root_dir=root) == [
            VersionEntry("26.2", "release"),
            VersionEntry("25w14a", "snapshot"),
            VersionEntry("b1.7.3", "old_beta"),
            VersionEntry("c0.0.13a", "old_alpha"),
        ]
        assert [e.is_release for e in remote_version_catalog(root_dir=root)] == [True, False, False, False]
        assert [e.channel for e in remote_version_catalog(root_dir=root)] == [
            "release",
            "snapshot",
            "snapshot",
            "snapshot",
        ]

    def test_missing_type_defaults_to_unknown(self, tmp_path) -> None:
        root = self._seed(tmp_path, {"versions": [{"id": "x", "url": "https://meta/x.json"}]})
        entry = remote_version_catalog(root_dir=root)[0]
        assert entry == VersionEntry("x", "unknown")
        assert not entry.is_release
        assert entry.channel == "snapshot"

    def test_empty_manifest(self, tmp_path) -> None:
        root = self._seed(tmp_path, {"versions": []})
        assert remote_version_catalog(root_dir=root) == []

    def test_missing_versions_key(self, tmp_path) -> None:
        root = self._seed(tmp_path, {})
        assert remote_version_catalog(root_dir=root) == []
