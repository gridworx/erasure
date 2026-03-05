"""Detect whether we are running in bootable mode or desktop mode."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Literal

BOOTABLE_SENTINEL = Path("/etc/erasure-live")
BOOTABLE_DATA_MOUNT = Path("/mnt/data")

Mode = Literal["bootable", "desktop"]


@dataclass
class Runtime:
    mode: Mode
    data_dir: Path
    is_root: bool = field(init=False)

    def __post_init__(self) -> None:
        self.is_root = os.geteuid() == 0 if hasattr(os, "geteuid") else False

    @property
    def can_wipe_internal(self) -> bool:
        return self.mode == "bootable"

    @property
    def can_wipe_external(self) -> bool:
        return self.is_root

    @property
    def can_manual_attestation(self) -> bool:
        return True


def detect_runtime(data_dir: Path | None = None) -> Runtime:
    """Determine the runtime context and locate the data directory."""
    if BOOTABLE_SENTINEL.exists():
        mode: Mode = "bootable"
        resolved_data = data_dir or BOOTABLE_DATA_MOUNT
    else:
        mode = "desktop"
        resolved_data = data_dir or _find_desktop_data_dir()

    resolved_data.mkdir(parents=True, exist_ok=True)
    return Runtime(mode=mode, data_dir=resolved_data)


def _find_desktop_data_dir() -> Path:
    """Search for a data directory in common locations."""
    candidates = [
        Path.cwd() / "erasure-data",
        Path.home() / "erasure-data",
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate
    return candidates[0]
