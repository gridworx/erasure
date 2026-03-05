"""Discover block devices and their capabilities."""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

DriveType = Literal["nvme", "sata_ssd", "sata_hdd", "usb", "unknown"]
SanitizeCapability = Literal["crypto_erase", "block_erase", "ata_secure_erase", "software_only"]


@dataclass
class DriveInfo:
    path: str  # e.g., "/dev/sda" or "/dev/nvme0n1"
    model: str = ""
    serial: str = ""
    firmware: str = ""
    capacity_bytes: int = 0
    interface: str = ""
    drive_type: DriveType = "unknown"
    is_boot_media: bool = False
    is_removable: bool = False
    sanitize_caps: list[SanitizeCapability] = None
    is_apple: bool = False

    def __post_init__(self) -> None:
        if self.sanitize_caps is None:
            self.sanitize_caps = []

    @property
    def capacity_human(self) -> str:
        if self.capacity_bytes == 0:
            return "Unknown"
        gb = self.capacity_bytes / (1000 ** 3)
        if gb >= 1000:
            return f"{gb / 1000:.1f} TB"
        return f"{gb:.0f} GB"

    @property
    def best_sanitize_method(self) -> SanitizeCapability:
        preference = ["crypto_erase", "block_erase", "ata_secure_erase", "software_only"]
        for method in preference:
            if method in self.sanitize_caps:
                return method
        return "software_only"


def discover_drives(exclude_usb_boot: bool = True) -> list[DriveInfo]:
    """Enumerate all block devices and detect capabilities."""
    try:
        return _discover_linux(exclude_usb_boot)
    except (FileNotFoundError, subprocess.SubprocessError):
        return []


def _discover_linux(exclude_usb_boot: bool) -> list[DriveInfo]:
    result = subprocess.run(
        ["lsblk", "-J", "-b", "-d", "-o",
         "NAME,MODEL,SERIAL,SIZE,TRAN,TYPE,RM,HOTPLUG,MOUNTPOINT"],
        capture_output=True, text=True, timeout=10,
    )
    if result.returncode != 0:
        return []

    data = json.loads(result.stdout)
    drives: list[DriveInfo] = []

    for dev in data.get("blockdevices", []):
        if dev.get("type") != "disk":
            continue

        transport = (dev.get("tran") or "").lower()
        name = dev["name"]
        path = f"/dev/{name}"

        is_removable = dev.get("rm", False) or dev.get("hotplug", False)
        is_boot = _is_boot_device(dev)

        if exclude_usb_boot and is_boot and transport == "usb":
            is_boot_flag = True
        else:
            is_boot_flag = is_boot

        model = (dev.get("model") or "").strip()
        is_apple = "apple" in model.lower()

        drive = DriveInfo(
            path=path,
            model=model,
            serial=(dev.get("serial") or "").strip(),
            capacity_bytes=int(dev.get("size") or 0),
            interface=transport.upper() or "Unknown",
            drive_type=_classify_drive(name, transport),
            is_boot_media=is_boot_flag,
            is_removable=is_removable,
            is_apple=is_apple,
        )
        drive.sanitize_caps = _detect_sanitize_caps(drive)
        drives.append(drive)

    return drives


def _classify_drive(name: str, transport: str) -> DriveType:
    if name.startswith("nvme"):
        return "nvme"
    if transport == "usb":
        return "usb"
    if transport in ("sata", "ata"):
        return "sata_ssd"  # refined later with rotational check
    return "unknown"


def _is_boot_device(dev: dict) -> bool:
    mp = dev.get("mountpoint") or ""
    return mp in ("/", "/boot", "/boot/efi") or "erasure" in mp.lower()


def _detect_sanitize_caps(drive: DriveInfo) -> list[SanitizeCapability]:
    caps: list[SanitizeCapability] = ["software_only"]

    if drive.is_apple:
        return caps

    if drive.drive_type == "nvme":
        caps.extend(_check_nvme_sanitize(drive.path))
    elif drive.drive_type in ("sata_ssd", "sata_hdd"):
        caps.extend(_check_ata_secure_erase(drive.path))

    return caps


def _check_nvme_sanitize(path: str) -> list[SanitizeCapability]:
    """Query NVMe identify controller for sanitize support."""
    caps: list[SanitizeCapability] = []
    try:
        result = subprocess.run(
            ["nvme", "id-ctrl", path, "-o", "json"],
            capture_output=True, text=True, timeout=5,
        )
        if result.returncode != 0:
            return caps
        ctrl = json.loads(result.stdout)
        sanicap = ctrl.get("sanicap", 0)
        if sanicap & 0x2:
            caps.append("block_erase")
        if sanicap & 0x4:
            caps.append("crypto_erase")
    except (FileNotFoundError, subprocess.TimeoutExpired, json.JSONDecodeError):
        pass
    return caps


def _check_ata_secure_erase(path: str) -> list[SanitizeCapability]:
    """Query ATA security feature set via hdparm."""
    try:
        result = subprocess.run(
            ["hdparm", "-I", path],
            capture_output=True, text=True, timeout=5,
        )
        if "supported: enhanced erase" in result.stdout.lower():
            return ["ata_secure_erase"]
        if "supported" in result.stdout.lower() and "security" in result.stdout.lower():
            return ["ata_secure_erase"]
    except (FileNotFoundError, subprocess.TimeoutExpired):
        pass
    return []


def mock_drives() -> list[DriveInfo]:
    """Return mock drives for development/testing."""
    return [
        DriveInfo(
            path="/dev/nvme0n1", model="Samsung 980 PRO", serial="S4EWNX0T812345",
            capacity_bytes=512_110_190_592, interface="NVMe", drive_type="nvme",
            sanitize_caps=["software_only", "block_erase", "crypto_erase"],
        ),
        DriveInfo(
            path="/dev/sda", model="WDC WD10EZEX-08WN4A0", serial="WD-WMC3T0123456",
            capacity_bytes=1_000_204_886_016, interface="SATA", drive_type="sata_hdd",
            sanitize_caps=["software_only"],
        ),
        DriveInfo(
            path="/dev/sdb", model="Samsung 870 EVO", serial="S6PENX0T999888",
            capacity_bytes=500_107_862_016, interface="SATA", drive_type="sata_ssd",
            sanitize_caps=["software_only", "ata_secure_erase"],
        ),
        DriveInfo(
            path="/dev/sdc", model="SanDisk Ultra", serial="AABBCCDD1122",
            capacity_bytes=32_015_679_488, interface="USB", drive_type="usb",
            is_boot_media=True, is_removable=True,
            sanitize_caps=["software_only"],
        ),
    ]
