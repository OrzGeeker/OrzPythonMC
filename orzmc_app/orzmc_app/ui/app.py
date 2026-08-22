"""Textual TUI: four tabs + footer log, driving only the library public API.

Long operations (launch / deploy / remove / backup) run in worker threads
(``@work(thread=True)``); their ``Reporter`` / ``ProgressSink`` output is
hopped onto the Textual event loop and rendered into a footer ``RichLog`` and a
``ProgressBar``. Destructive actions confirm on the main thread (async modal)
before a worker starts.
"""

from __future__ import annotations

import threading
from typing import ClassVar

from textual import work
from textual.app import App, ComposeResult
from textual.binding import BindingType
from textual.widgets import Footer, Header, ProgressBar, RichLog, Tab, TabbedContent

from orzmc import (
    RuntimeOptions,
    backup_world,
    deploy_server,
    launch_client,
    list_versions,
    remote_versions,
    remove_version,
)
from orzmc_app.ui.log import TuiReporter
from orzmc_app.ui.progress import TuiProgressSink
from orzmc_app.ui.screens import ClientTab, ConfirmScreen, OpsTab, ServerTab, SettingsTab


class OrzMCApp(App):
    """The main OrzMC TUI window."""

    TITLE = "OrzMC"
    SUB_TITLE = "Minecraft 客户端 / 服务端工具"

    CSS = """
    Screen { layout: vertical; }
    TabbedContent { height: 1fr; }
    #pb { margin: 0 1; height: 1; }
    #log {
        height: 10;
        border: round $accent;
        background: $surface;
        margin: 0 1;
    }
    """

    BINDINGS: ClassVar[list[BindingType]] = [
        ("q", "quit", "退出"),
        ("ctrl+c", "quit", "退出"),
    ]

    def __init__(self, root_dir: str | None = None) -> None:
        super().__init__()
        self.root_dir = root_dir
        self.reporter = TuiReporter(self._hop_log)
        self.sink = TuiProgressSink(self._hop_progress)
        self._log_widget: RichLog | None = None
        self._bar_widget: ProgressBar | None = None
        # The app is created and run() in the same thread (Textual pattern);
        # child widget on_mount fires before App.on_mount, so capture it here.
        self._app_thread: int = threading.get_ident()

    def compose(self) -> ComposeResult:
        yield Header()
        with TabbedContent():
            with Tab("客户端"):
                yield ClientTab()
            with Tab("服务端"):
                yield ServerTab()
            with Tab("运维"):
                yield OpsTab()
            with Tab("设置"):
                yield SettingsTab()
        yield ProgressBar(id="pb")
        yield RichLog(id="log", highlight=True, markup=True, wrap=True)
        yield Footer()

    def on_mount(self) -> None:
        self._log_widget = self.query_one("#log", RichLog)
        self._bar_widget = self.query_one("#pb", ProgressBar)

    # ── thread → main hops ──────────────────────────────────────────────────

    def _hop_log(self, text: str, style: str) -> None:
        if threading.get_ident() == self._app_thread:
            self._append_log(text, style)  # already on the app thread
        else:
            self.call_from_thread(self._append_log, text, style)

    def _hop_progress(self, desc: str | None, total: int | None, advance: int | None) -> None:
        if threading.get_ident() == self._app_thread:
            self._apply_progress(desc, total, advance)
        else:
            self.call_from_thread(self._apply_progress, desc, total, advance)

    def log_text(self, text: str, style: str = "") -> None:
        """Write into the footer log (thread-safe)."""
        self._hop_log(text, style)

    def _append_log(self, text: str, style: str) -> None:
        if self._log_widget is None:
            return
        if style:
            self._log_widget.write(f"[{style}]{text}[/]")
        else:
            self._log_widget.write(text)

    def _apply_progress(self, desc: str | None, total: int | None, advance: int | None) -> None:
        if self._bar_widget is None:
            return
        if desc is not None:
            self._append_log(desc, "info")
            self._bar_widget.update(total=total, progress=0)
        if advance:
            self._bar_widget.advance(advance)
        if desc is None and total is None and advance is None:
            self._bar_widget.update(progress=self._bar_widget.total or 0)

    async def ask_confirm(self, prompt: str) -> bool:
        """Show a confirm modal (main thread) and await the answer."""
        return await self.push_screen_wait(ConfirmScreen(prompt))

    # ── actions from tabs ───────────────────────────────────────────────────

    def run_client(self, options: RuntimeOptions) -> None:
        self.log_text("正在启动客户端...", "info")
        self._client_worker(options)

    def run_server(self, options: RuntimeOptions) -> None:
        self.log_text("正在部署/启动服务端...", "info")
        self._server_worker(options)

    def run_remove(self, version: str) -> None:
        self._remove_worker(version)

    def run_backup(self, version: str) -> None:
        self._backup_worker(version)

    def run_refresh_cache(self) -> None:
        self.log_text("正在刷新 Mojang 版本缓存...", "info")
        self._cache_worker()

    @work(thread=True, exclusive=True)
    def _client_worker(self, options: RuntimeOptions) -> None:
        try:
            launch_client(options, reporter=self.reporter, sink=self.sink)
            self.log_text("客户端已退出", "plain")
        except Exception as exc:
            self.log_text(f"错误: {exc}", "error")

    @work(thread=True, exclusive=True)
    def _server_worker(self, options: RuntimeOptions) -> None:
        try:
            deploy_server(
                options,
                reporter=self.reporter,
                sink=self.sink,
                on_line=lambda line: self.log_text(line, "server"),
            )
            self.log_text("服务端进程已退出", "plain")
        except Exception as exc:
            self.log_text(f"错误: {exc}", "error")

    @work(thread=True)
    def _remove_worker(self, version: str) -> None:
        try:
            installed = list_versions(root_dir=self.root_dir)
            match = next((v for v in installed if v.version == version), None)
            if match is None:
                self.log_text(f"未找到已安装版本 {version}", "warn")
                return
            if match.has_client:
                remove_version(version, is_client=True, yes=True, root_dir=self.root_dir)
            for server_type in match.server_types:
                remove_version(version, is_client=False, game_type=server_type, yes=True, root_dir=self.root_dir)
            self.log_text(f"已移除 {version}", "success")
        except Exception as exc:
            self.log_text(f"错误: {exc}", "error")
        finally:
            self.call_from_thread(self._refresh_ops)

    @work(thread=True)
    def _backup_worker(self, version: str) -> None:
        try:
            installed = list_versions(root_dir=self.root_dir)
            match = next((v for v in installed if v.version == version), None)
            if match is None or not match.server_types:
                self.log_text(f"{version} 没有可备份的服务端世界", "warn")
                return
            server_type = match.server_types[0]
            dest = backup_world(version, game_type=server_type, root_dir=self.root_dir)
            self.log_text(f"备份完成: {dest}", "success")
        except Exception as exc:
            self.log_text(f"错误: {exc}", "error")

    @work(thread=True)
    def _cache_worker(self) -> None:
        try:
            versions = remote_versions(root_dir=self.root_dir, update=True)
            self.log_text(f"版本缓存已刷新,共 {len(versions)} 个 release", "success")
        except Exception as exc:
            self.log_text(f"刷新失败: {exc}", "error")

    # ── helpers ─────────────────────────────────────────────────────────────

    def _refresh_ops(self) -> None:
        for tab in self.query(OpsTab):
            tab._refresh_list()
            tab._refresh_java()
