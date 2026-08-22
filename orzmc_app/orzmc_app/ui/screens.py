"""TUI tabs (客户端 / 服务端 / 运维 / 设置) + confirm modal.

Tabs collect input and hand a ``RuntimeOptions`` (or a version id) to the
``OrzMCApp``; they never touch the library services directly.
"""

from __future__ import annotations

import os
from typing import TYPE_CHECKING, cast

from textual.app import ComposeResult
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import (
    Button,
    Input,
    Label,
    ListItem,
    ListView,
    RadioButton,
    RadioSet,
    Static,
    Switch,
)

from orzmc import DEFAULT_ROOT, InstalledVersion, PathLayout, RuntimeOptions, list_versions

if TYPE_CHECKING:
    from orzmc_app.ui.app import OrzMCApp

# ── small labelled input / switch fields ─────────────────────────────────────


class AppTab(VerticalScroll):
    """Base for tabs: exposes the concrete ``OrzMCApp`` as ``self.orzmc``.

    ``self.app`` from Textual is typed ``App[object]``; ``orzmc`` casts it to
    the real app so the tabs can call its public helpers.
    """

    @property
    def orzmc(self) -> OrzMCApp:
        return cast("OrzMCApp", self.app)


class Field(Vertical):
    """A labelled single-line input."""

    def __init__(self, label: str, *, value: str = "", placeholder: str = "", widget_id: str = "") -> None:
        super().__init__()
        self._label_text = label
        self._value = value
        self._placeholder = placeholder
        self._widget_id = widget_id

    def compose(self) -> ComposeResult:
        yield Label(self._label_text)
        yield Input(value=self._value, placeholder=self._placeholder, id=self._widget_id)


class SwitchField(Horizontal):
    """A labelled on/off switch."""

    def __init__(self, label: str, *, value: bool = False, widget_id: str = "") -> None:
        super().__init__()
        self._label_text = label
        self._value = value
        self._widget_id = widget_id

    def compose(self) -> ComposeResult:
        yield Switch(value=self._value, id=self._widget_id)
        yield Label(self._label_text, classes="switch-label")


# ── 客户端 tab ───────────────────────────────────────────────────────────────


class ClientTab(AppTab):
    DEFAULT_CSS = """
    ClientTab { padding: 1 2; }
    ClientTab Field { margin-bottom: 1; }
    ClientTab #client-launch { margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Field("版本(留空 = 最新)", placeholder="例如 1.20.4", widget_id="client-version")
        yield Field("用户名", value="guest", widget_id="client-username")
        yield Label("类型")
        yield RadioSet(RadioButton("原版", value=True), RadioButton("Forge"), id="client-type")
        with Horizontal(id="client-mem"):
            yield Field("最小内存", value="512M", widget_id="client-minmem")
            yield Field("最大内存", value="2G", widget_id="client-maxmem")
        yield SwitchField("OptiFine", widget_id="client-optifine")
        yield SwitchField("Fabric", widget_id="client-fabric")
        yield SwitchField("提取音乐后退出", widget_id="client-music")
        yield Button("启动客户端", variant="primary", id="client-launch")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "client-launch":
            return
        options = RuntimeOptions(
            is_client=True,
            version=self._value("#client-version") or None,
            username=self._value("#client-username") or "guest",
            game_type="forge" if self.query_one("#client-type", RadioSet).pressed_index == 1 else "vanilla",
            min_mem=self._value("#client-minmem") or "512M",
            max_mem=self._value("#client-maxmem") or "2G",
            optifine=self._switch("#client-optifine"),
            fabric=self._switch("#client-fabric"),
            extract_music=self._switch("#client-music"),
            root_dir=self.orzmc.root_dir,
        )
        self.orzmc.run_client(options)

    def _value(self, widget_id: str) -> str:
        return self.query_one(widget_id, Input).value.strip()

    def _switch(self, widget_id: str) -> bool:
        return self.query_one(widget_id, Switch).value


# ── 服务端 tab ───────────────────────────────────────────────────────────────


class ServerTab(AppTab):
    DEFAULT_CSS = """
    ServerTab { padding: 1 2; }
    ServerTab Field { margin-bottom: 1; }
    ServerTab #server-deploy { margin-top: 1; }
    """

    def compose(self) -> ComposeResult:
        yield Field("版本(留空 = 最新)", placeholder="例如 1.20.4", widget_id="server-version")
        yield Label("类型")
        yield RadioSet(
            RadioButton("原版", value=True),
            RadioButton("Paper"),
            RadioButton("Spigot"),
            RadioButton("Forge"),
            id="server-type",
        )
        with Horizontal(id="server-mem"):
            yield Field("最小内存", value="512M", widget_id="server-minmem")
            yield Field("最大内存", value="2G", widget_id="server-maxmem")
        yield SwitchField("同意 EULA(--yes)", widget_id="server-yes")
        yield SwitchField("世界升级(--forceUpgrade)", widget_id="server-force-upgrade")
        yield SwitchField("软链接备份世界(--symlink)", widget_id="server-symlink")
        yield SwitchField("强制重新下载(--force-download)", widget_id="server-force-download")
        yield Button("部署服务端", variant="primary", id="server-deploy")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "server-deploy":
            return
        types = ("vanilla", "paper", "spigot", "forge")
        options = RuntimeOptions(
            is_client=False,
            version=self._value("#server-version") or None,
            game_type=types[self.query_one("#server-type", RadioSet).pressed_index],
            min_mem=self._value("#server-minmem") or "512M",
            max_mem=self._value("#server-maxmem") or "2G",
            yes=self._switch("#server-yes"),
            force_upgrade=self._switch("#server-force-upgrade"),
            symlink=self._switch("#server-symlink"),
            force_download=self._switch("#server-force-download"),
            root_dir=self.orzmc.root_dir,
        )
        self.orzmc.run_server(options)

    def _value(self, widget_id: str) -> str:
        return self.query_one(widget_id, Input).value.strip()

    def _switch(self, widget_id: str) -> bool:
        return self.query_one(widget_id, Switch).value


# ── 运维 tab ─────────────────────────────────────────────────────────────────


class OpsTab(AppTab):
    DEFAULT_CSS = """
    OpsTab { padding: 1 2; }
    .ops-title { text-style: bold; margin-top: 1; }
    #ops-list { height: 10; border: round $primary; }
    #ops-actions { margin: 1 0; }
    #ops-actions Button { margin-right: 1; }
    """

    def __init__(self) -> None:
        super().__init__()
        self._versions: list[InstalledVersion] = []

    def compose(self) -> ComposeResult:
        yield Label("已安装版本", classes="ops-title")
        yield ListView(id="ops-list")
        with Horizontal(id="ops-actions"):
            yield Button("刷新", id="ops-refresh")
            yield Button("移除所选", variant="error", id="ops-remove")
            yield Button("备份世界", id="ops-backup")
            yield Button("刷新版本缓存", id="ops-cache")
        yield Label("Java 运行时", classes="ops-title")
        yield Static(id="ops-java")

    def on_mount(self) -> None:
        self._refresh_list()
        self._refresh_java()

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "ops-refresh":
            self._refresh_list()
        elif event.button.id == "ops-remove":
            selected = self._selected()
            if selected is None:
                return
            if await self.orzmc.ask_confirm(f"确定移除 {selected.version} 的全部内容吗?"):
                self.orzmc.run_remove(selected.version)
        elif event.button.id == "ops-backup":
            selected = self._selected()
            if selected is not None:
                self.orzmc.run_backup(selected.version)
        elif event.button.id == "ops-cache":
            self.orzmc.run_refresh_cache()

    def _refresh_list(self) -> None:
        self._versions = list_versions(root_dir=self.orzmc.root_dir)
        lv = self.query_one("#ops-list", ListView)
        lv.clear()
        for item in self._versions:
            lv.append(ListItem(Label(item.describe())))
        self.orzmc.log_text(f"共 {len(self._versions)} 个已安装版本", "info")

    def _refresh_java(self) -> None:
        widget = self.query_one("#ops-java", Static)
        root = self.orzmc.root_dir or DEFAULT_ROOT
        java_dir = PathLayout(root=root, version="", game_type="vanilla").java_dir()
        if not os.path.isdir(java_dir):
            widget.update("未安装托管 Java(运行时会自动安装到应用目录)")
            return
        majors = sorted(os.listdir(java_dir))
        widget.update(f"已安装: {', '.join(majors)}")

    def _selected(self) -> InstalledVersion | None:
        index = self.query_one("#ops-list", ListView).index
        if index is None or index < 0 or index >= len(self._versions):
            self.orzmc.log_text("请先在列表选择一个版本", "warn")
            return None
        return self._versions[index]


# ── 设置 tab ─────────────────────────────────────────────────────────────────


class SettingsTab(AppTab):
    DEFAULT_CSS = """
    SettingsTab { padding: 1 2; }
    SettingsTab Field { margin-bottom: 1; }
    SettingsTab #settings-hint { margin-top: 1; color: $text-muted; }
    """

    def compose(self) -> ComposeResult:
        yield Label("游戏根目录(所有文件都存到这里)")
        yield Field("", value="", placeholder=str(DEFAULT_ROOT), widget_id="settings-root")
        yield Button("保存设置", id="settings-save")
        yield Static(
            "目录结构: versions/<版本>/client|server/<类型>、java/<大版本>/、cache/、backup/。"
            "Java 运行时会自动安装到应用目录,不依赖系统 Java。",
            id="settings-hint",
        )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id != "settings-save":
            return
        value = self.query_one("#settings-root", Input).value.strip()
        self.orzmc.root_dir = value or None
        target = value or str(DEFAULT_ROOT)
        self.orzmc.log_text(f"游戏根目录已设置为 {target}", "success")


# ── confirm modal ────────────────────────────────────────────────────────────


class ConfirmScreen(ModalScreen[bool]):
    """A modal yes/no prompt used for destructive actions."""

    DEFAULT_CSS = """
    ConfirmScreen { align: center middle; }
    #confirm-box {
        width: 62%;
        height: auto;
        border: round $primary;
        background: $surface;
        padding: 1 2;
    }
    #confirm-prompt { margin-bottom: 1; text-style: bold; }
    #confirm-actions { align: center middle; height: 3; }
    #confirm-actions Button { margin: 0 1; }
    """

    def __init__(self, prompt: str, *, ok_label: str = "确认", cancel_label: str = "取消") -> None:
        super().__init__()
        self._prompt = prompt
        self._ok = ok_label
        self._cancel = cancel_label

    def compose(self) -> ComposeResult:
        yield Label(self._prompt, id="confirm-prompt")
        with Horizontal(id="confirm-actions"):
            yield Button(self._ok, variant="primary", id="confirm-ok")
            yield Button(self._cancel, variant="error", id="confirm-cancel")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "confirm-ok")
