"""Typer CLI entry point for orzmc-app.

The console script ``orzmc`` maps to :func:`main`.
"""

from __future__ import annotations

import sys

import typer

from orzmc_app.cli.app import app


def main() -> int:
    try:
        app()
        return 0
    except typer.Exit as exc:
        return exc.exit_code or 0
    except KeyboardInterrupt:
        print("已取消", file=sys.stderr)
        return 130
    except Exception:  # pragma: no cover - unexpected bug, keep a traceback
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
