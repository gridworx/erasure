"""Match drives and systems against assets.csv."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class AssetRecord:
    """A single row from assets.csv with whatever columns are present."""

    system_serial: str = ""
    asset_tag: str = ""
    hostname: str = ""
    system_model: str = ""
    assigned_user: str = ""
    drive_serial: str = ""
    disposition_method: str = ""
    ticket_number: str = ""
    raw: dict[str, str] = field(default_factory=dict)


class AssetMatcher:
    """Load and match assets from a CSV file."""

    def __init__(self, data_dir: Path) -> None:
        self._assets: list[AssetRecord] = []
        self._by_system_serial: dict[str, AssetRecord] = {}
        self._by_drive_serial: dict[str, AssetRecord] = {}
        self._assigned: set[str] = set()
        self._load(data_dir / "assets.csv")

    def _load(self, path: Path) -> None:
        if not path.is_file():
            return
        with open(path, newline="", encoding="utf-8-sig") as f:
            for row in csv.DictReader(f):
                record = AssetRecord(
                    system_serial=row.get("system_serial", "").strip(),
                    asset_tag=row.get("asset_tag", "").strip(),
                    hostname=row.get("hostname", "").strip(),
                    system_model=row.get("system_model", "").strip(),
                    assigned_user=row.get("assigned_user", "").strip(),
                    drive_serial=row.get("drive_serial", "").strip(),
                    disposition_method=row.get("disposition_method", "").strip(),
                    ticket_number=row.get("ticket_number", "").strip(),
                    raw=dict(row),
                )
                self._assets.append(record)
                if record.system_serial:
                    self._by_system_serial[record.system_serial.upper()] = record
                if record.drive_serial:
                    self._by_drive_serial[record.drive_serial.upper()] = record

    def match_by_system_serial(self, serial: str) -> AssetRecord | None:
        return self._by_system_serial.get(serial.strip().upper())

    def match_by_drive_serial(self, serial: str) -> AssetRecord | None:
        return self._by_drive_serial.get(serial.strip().upper())

    def unassigned_assets(self) -> list[AssetRecord]:
        """Assets not yet paired to a drive in this session."""
        return [a for a in self._assets if a.system_serial not in self._assigned]

    def mark_assigned(self, system_serial: str) -> None:
        self._assigned.add(system_serial.upper())

    @property
    def total(self) -> int:
        return len(self._assets)

    @property
    def loaded(self) -> bool:
        return len(self._assets) > 0
