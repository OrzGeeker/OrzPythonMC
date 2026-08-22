"""Services: JavaEnv, Downloader, ServerService arg assembly, ClientService classpath.

All tests use a real tmp root + fakes for network; no system java is touched.
"""

from __future__ import annotations

import io
import os
import tarfile

from fakes import FakeHttp, FakeReporter, FakeSink

from orzmc import (
    ClientService,
    FileStore,
    PathLayout,
    RuntimeOptions,
    ServerService,
    Services,
    resolve_libraries,
)
from orzmc.services.java import JavaEnv


def _services(tmp_path, reporter: FakeReporter, sink: FakeSink, http: FakeHttp, **options) -> Services:
    base = RuntimeOptions(root_dir=str(tmp_path), version="1.20.4", **options)
    return Services(base, reporter=reporter, sink=sink, http=http, fs=FileStore())


class TestJavaEnv:
    def test_resolve_existing_runtime(self, tmp_path, reporter, sink) -> None:
        fs = FileStore()
        paths = PathLayout(root=str(tmp_path))
        fs.write_text(paths.java_bin(17), "#!/bin/sh\n")
        http = FakeHttp()
        env = JavaEnv(http, fs, reporter, sink, paths)
        assert env.resolve(17, need_jdk=True) == paths.java_bin(17)
        assert http.requests == []

    def test_resolve_refused_by_confirm(self, tmp_path, reporter, sink) -> None:
        env = JavaEnv(FakeHttp(), FileStore(), reporter, sink, PathLayout(root=str(tmp_path)))
        with pytest_raises(RuntimeError):
            env.resolve(17, confirm=lambda major, jdk: False)

    def test_resolve_installs_and_caches(self, tmp_path, reporter, sink, http) -> None:
        # seed a fake JDK archive (Adoptium layout: single top-level dir)
        archive = _make_tar_gz(
            {"jdk-17.0.1/bin/java": "#!/bin/sh\necho 17\n", "jdk-17.0.1/release": "JAVA_VERSION=17\n"}
        )
        http.canned_archive = archive
        fs = FileStore()
        paths = PathLayout(root=str(tmp_path))
        env = JavaEnv(http, fs, reporter, sink, paths)
        java = env.resolve(17, need_jdk=True)
        assert java == paths.java_bin(17)
        assert fs.is_file(java)
        # second resolve must not hit the network
        http.requests.clear()
        assert env.resolve(17) == java
        assert http.requests == []

    def test_install_uses_jre_by_default(self, tmp_path, reporter, sink, http) -> None:
        http.canned_archive = _make_tar_gz({"jre-8/bin/java": "java\n"})
        fs = FileStore()
        paths = PathLayout(root=str(tmp_path))
        env = JavaEnv(http, fs, reporter, sink, paths)
        env.resolve(8, need_jdk=False)
        assert fs.is_file(paths.java_bin(8))


class TestDownloader:
    def test_prepare_client(self, tmp_path, reporter, sink, http) -> None:
        http.canned_archive = b"{}"  # used for both the client jar and the index json
        services = _services(tmp_path, reporter, sink, http)
        version_json = {
            "downloads": {"client": {"url": "https://client.jar", "sha1": None}},
            "assetIndex": {"id": "1.20", "url": "https://index.json", "sha1": None},
            "libraries": [],
            "arguments": {"game": [], "jvm": []},
        }
        services.downloader.prepare_client(version_json)
        paths = services.context.paths
        assert services.fs.is_file(paths.client_jar_path())
        assert services.fs.is_file(os.path.join(paths.client_indexes_dir(), "1.20.json"))
        # asset objects index was read (empty) → nothing else downloaded
        assert len(http.requests) == 2

    def test_download_file_skips_existing(self, tmp_path, reporter, sink, http) -> None:
        http.canned_archive = b"data"
        services = _services(tmp_path, reporter, sink, http)
        dest = services.context.paths.client_jar_path()
        assert services.downloader.download_file("https://x", dest, "x")
        assert not services.downloader.download_file("https://x", dest, "x")  # cached
        assert len(http.requests) == 1


class TestServerService:
    def test_build_server_command(self, tmp_path, reporter, sink, http) -> None:
        services = _services(
            tmp_path,
            reporter,
            sink,
            http,
            server_args="nogui --port 25565",
            jvm_opts="-XX:+UseZGC",
            force_upgrade=True,
        )
        server = ServerService(services)
        cmd = server._build_server_command("/managed/java")
        assert cmd[0] == "/managed/java"
        assert cmd.index("-XX:+UseZGC") < cmd.index("-jar")
        assert "-Xmx2G" in cmd
        assert "-jar" in cmd
        assert "nogui" in cmd and "--port" in cmd and "25565" in cmd
        assert cmd[-1] == "--forceUpgrade"

    def test_accept_eula_via_yes(self, tmp_path, reporter, sink, http) -> None:
        services = _services(tmp_path, reporter, sink, http, yes=True)
        server = ServerService(services)
        server._accept_eula(confirm_eula=None)
        assert services.fs.read_text(services.context.paths.server_eula_path()) == "eula=true\n"

    def test_accept_eula_requires_yes_or_confirm(self, tmp_path, reporter, sink, http) -> None:
        services = _services(tmp_path, reporter, sink, http, yes=False)
        server = ServerService(services)
        with pytest_raises(RuntimeError):
            server._accept_eula(confirm_eula=None)

    def test_accept_eula_uses_confirm(self, tmp_path, reporter, sink, http) -> None:
        services = _services(tmp_path, reporter, sink, http, yes=False)
        server = ServerService(services)
        server._accept_eula(confirm_eula=lambda: True)
        assert services.fs.read_text(services.context.paths.server_eula_path()) == "eula=true\n"

    def test_write_server_properties_idempotent(self, tmp_path, reporter, sink, http) -> None:
        services = _services(tmp_path, reporter, sink, http)
        server = ServerService(services)
        server._write_server_properties()
        server._write_server_properties()
        content = services.fs.read_text(services.context.paths.server_properties_path())
        assert content.count("online-mode=false") == 1


class TestClientService:
    def test_build_classpath(self, tmp_path, reporter, sink, http) -> None:
        services = _services(tmp_path, reporter, sink, http)
        paths = services.context.paths
        fs = services.fs
        fs.write_text(paths.client_jar_path(), "jar")
        lib = resolve_libraries({"libraries": [{"name": "com.example:lib1:1.0"}]}, os_name="linux")[0]
        fs.write_text(paths.client_library_path(lib.path), "lib")

        client = ClientService(services)
        classpath = client._build_classpath(
            {"libraries": [{"name": "com.example:lib1:1.0"}], "arguments": {"game": [], "jvm": []}}, None
        )
        assert paths.client_jar_path() in classpath
        assert paths.client_library_path(lib.path) in classpath

    def test_run_requires_version(self, tmp_path, reporter, sink, http) -> None:
        # a client run on an empty root must raise a clear error, not hang on the network
        services = Services(
            RuntimeOptions(root_dir=str(tmp_path), version="1.20.4"),
            reporter=reporter,
            sink=sink,
            http=http,
            fs=FileStore(),
        )
        with pytest_raises(RuntimeError):
            ClientService(services).run()


def _make_tar_gz(files: dict[str, str]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz") as tf:
        for path, content in files.items():
            data = content.encode("utf-8")
            info = tarfile.TarInfo(path)
            info.size = len(data)
            info.mode = 0o755
            tf.addfile(info, io.BytesIO(data))
    return buf.getvalue()


def pytest_raises(exc):
    from pytest import raises

    return raises(exc)
