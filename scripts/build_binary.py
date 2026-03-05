#!/usr/bin/env python3
"""Build standalone binary for desktop mode distribution.

Creates a single executable that runs without Python installed.
Uses PyInstaller (simplest) or Nuitka (better performance, fewer AV false positives).

Usage:
    python scripts/build_binary.py [--nuitka]
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
ENTRY = ROOT / "erasure_ctl" / "__main__.py"
TEMPLATES = ROOT / "erasure_ctl" / "reports" / "templates"


def build_pyinstaller() -> None:
    """Build with PyInstaller (default)."""
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--name", "erasure-ctl",
        "--add-data", f"{TEMPLATES}{_sep()}erasure_ctl/reports/templates",
        "--hidden-import", "erasure_ctl",
        "--hidden-import", "erasure_ctl.core",
        "--hidden-import", "erasure_ctl.core.runtime",
        "--hidden-import", "erasure_ctl.core.config",
        "--hidden-import", "erasure_ctl.core.asset_matcher",
        "--hidden-import", "erasure_ctl.core.dmi",
        "--hidden-import", "erasure_ctl.core.discovery",
        "--hidden-import", "erasure_ctl.reports.generator",
        "--hidden-import", "erasure_ctl.tui.app",
        str(ENTRY),
    ]
    print(f"Building with PyInstaller...")
    print(f"  {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    print(f"\nBinary created: dist/erasure-ctl{_ext()}")


def build_nuitka() -> None:
    """Build with Nuitka (better performance, fewer AV issues)."""
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--output-filename=erasure-ctl",
        "--include-package=erasure_ctl",
        f"--include-data-dir={TEMPLATES}=erasure_ctl/reports/templates",
        str(ENTRY),
    ]
    print(f"Building with Nuitka...")
    print(f"  {' '.join(cmd)}")
    subprocess.run(cmd, check=True, cwd=str(ROOT))
    print(f"\nBinary created: erasure-ctl{_ext()}")


def _sep() -> str:
    return ";" if sys.platform == "win32" else ":"


def _ext() -> str:
    return ".exe" if sys.platform == "win32" else ""


if __name__ == "__main__":
    if "--nuitka" in sys.argv:
        build_nuitka()
    else:
        build_pyinstaller()
