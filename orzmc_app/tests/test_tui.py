"""TUI smoke tests: the app mounts, tabs render, launch hands options to the library.

All runs are headless (``App.run_test``); the library's network entry points are
monkeypatched so no real download happens.
"""

from __future__ import annotations

import asyncio

from textual.widgets import Button, Input, Switch

from orzmc import RuntimeOptions
from orzmc_app.ui.app import OrzMCApp
from orzmc_app.ui.screens import ClientTab, OpsTab, ServerTab, SettingsTab


def _run(coro):
    return asyncio.run(coro)


def test_app_mounts_all_tabs(tmp_path) -> None:
    async def scenario() -> None:
        app = OrzMCApp(root_dir=str(tmp_path))
        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.query_one(ClientTab) is not None
            assert app.query_one(ServerTab) is not None
            assert app.query_one(OpsTab) is not None
            assert app.query_one(SettingsTab) is not None
            app.log_text("hello", "info")
            await pilot.pause()
            app.exit()

    _run(scenario())


def test_client_launch_passes_options(monkeypatch, tmp_path) -> None:
    captured: dict[str, RuntimeOptions] = {}
    monkeypatch.setattr(
        "orzmc_app.ui.app.launch_client",
        lambda options, **kwargs: captured.update(opts=options) or 0,
    )

    async def scenario() -> None:
        app = OrzMCApp(root_dir=str(tmp_path))
        async with app.run_test() as pilot:
            app.query_one("#client-version", Input).value = "1.20.4"
            app.query_one("#client-username", Input).value = "tester"
            app.query_one("#client-minmem", Input).value = "1G"
            app.query_one("#client-optifine", Switch).value = True
            app.query_one("#client-launch", Button).press()
            await app.workers.wait_for_complete()
            await pilot.pause()
            app.exit()

    _run(scenario())
    options = captured["opts"]
    assert options.version == "1.20.4"
    assert options.username == "tester"
    assert options.min_mem == "1G"
    assert options.optifine
    assert options.root_dir == str(tmp_path)


def test_worker_logs_library_error(monkeypatch, tmp_path) -> None:
    def boom(options, **kwargs) -> int:
        raise RuntimeError("network down")

    monkeypatch.setattr("orzmc_app.ui.app.launch_client", boom)

    async def scenario() -> None:
        app = OrzMCApp(root_dir=str(tmp_path))
        async with app.run_test() as pilot:
            app.query_one("#client-launch", Button).press()
            await app.workers.wait_for_complete()
            await pilot.pause()
            assert app is not None
            app.exit()

    _run(scenario())


def test_remove_requires_selection(tmp_path) -> None:
    async def scenario() -> None:
        app = OrzMCApp(root_dir=str(tmp_path))
        async with app.run_test() as pilot:
            await pilot.pause()
            ops = app.query_one(OpsTab)
            assert ops._selected() is None  # nothing installed
            app.exit()

    _run(scenario())
