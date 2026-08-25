"""Build the orzmc-app into a single-file PyInstaller binary → dist/.

Run from the workspace root: `uv run --package orzmc-app python scripts/build.py`
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def main() -> int:
    dist = ROOT / "dist"
    build_dir = ROOT / ".pybuild"
    for d in (dist, build_dir):
        if d.exists():
            shutil.rmtree(d)
    dist.mkdir(parents=True, exist_ok=True)

    # Entry point: orzmc_app/orzmc_app/cli/__main__.py (package layout)
    entry = ROOT / "orzmc_app" / "orzmc_app" / "cli" / "__main__.py"
    if not entry.exists():
        print(f"Entry point not found: {entry}", file=sys.stderr)
        return 1

    cmd = [
        sys.executable,
        "-m",
        "PyInstaller",
        "--onefile",
        "--name",
        "orzmc",
        "--distpath",
        str(dist),
        "--workpath",
        str(build_dir),
        "--specpath",
        str(build_dir),
        "--clean",
        "--noconfirm",
        str(entry),
    ]
    result = subprocess.run(cmd, cwd=str(ROOT))
    if result.returncode != 0:
        print("PyInstaller build failed", file=sys.stderr)
        return result.returncode

    binary = dist / ("orzmc.exe" if sys.platform == "win32" else "orzmc")
    print(f"Binary: {binary}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
