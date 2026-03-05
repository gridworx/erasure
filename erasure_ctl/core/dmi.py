"""Read system identity from DMI/SMBIOS (Linux sysfs or dmidecode)."""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

DMI_PATH = Path("/sys/class/dmi/id")


@dataclass
class SystemInfo:
    manufacturer: str = ""
    model: str = ""
    serial: str = ""
    asset_tag: str = ""
    board_serial: str = ""
    bios_version: str = ""
    chassis_type: str = ""

    @property
    def display_name(self) -> str:
        parts = [p for p in (self.manufacturer, self.model) if p]
        return " ".join(parts) or "Unknown System"


def read_dmi() -> SystemInfo:
    """Read DMI fields. Falls back to dmidecode if sysfs unavailable."""
    if DMI_PATH.is_dir():
        return _read_from_sysfs()
    return _read_from_dmidecode()


def _read_sysfs_file(name: str) -> str:
    path = DMI_PATH / name
    try:
        return path.read_text(encoding="utf-8").strip()
    except (OSError, PermissionError):
        return ""


def _read_from_sysfs() -> SystemInfo:
    return SystemInfo(
        manufacturer=_read_sysfs_file("sys_vendor"),
        model=_read_sysfs_file("product_name"),
        serial=_read_sysfs_file("product_serial"),
        asset_tag=_read_sysfs_file("chassis_asset_tag"),
        board_serial=_read_sysfs_file("board_serial"),
        bios_version=_read_sysfs_file("bios_version"),
        chassis_type=_read_sysfs_file("chassis_type"),
    )


def _dmidecode_string(keyword: str) -> str:
    try:
        result = subprocess.run(
            ["dmidecode", "-s", keyword],
            capture_output=True,
            text=True,
            timeout=5,
        )
        return result.stdout.strip() if result.returncode == 0 else ""
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return ""


def _read_from_dmidecode() -> SystemInfo:
    return SystemInfo(
        manufacturer=_dmidecode_string("system-manufacturer"),
        model=_dmidecode_string("system-product-name"),
        serial=_dmidecode_string("system-serial-number"),
        asset_tag=_dmidecode_string("chassis-asset-tag"),
        board_serial=_dmidecode_string("baseboard-serial-number"),
        bios_version=_dmidecode_string("bios-version"),
    )


def mock_dmi() -> SystemInfo:
    """Return mock DMI data for development/testing."""
    return SystemInfo(
        manufacturer="HP Inc.",
        model="HP EliteBook 840 G8",
        serial="5CG1234XYZ",
        asset_tag="",
        board_serial="PWRFG1234",
        bios_version="T76 Ver. 01.05.00",
        chassis_type="10",
    )
