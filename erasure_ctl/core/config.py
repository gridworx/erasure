"""Load configuration from fixed-name CSV files on the data directory."""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass
class CompanyInfo:
    name: str = ""
    address: str = ""
    phone: str = ""
    website: str = ""
    email: str = ""


@dataclass
class Operator:
    operator_id: str = ""
    name: str = ""
    email: str = ""


@dataclass
class Settings:
    default_method: str = "auto"
    default_rounds: int = 1
    default_verify: str = "last"
    report_format: str = "pdf"
    exclude_usb: bool = True


@dataclass
class ErasureConfig:
    company: CompanyInfo = field(default_factory=CompanyInfo)
    operators: list[Operator] = field(default_factory=list)
    settings: Settings = field(default_factory=Settings)
    logo_path: Path | None = None
    data_dir: Path = field(default_factory=lambda: Path("."))


def load_config(data_dir: Path) -> ErasureConfig:
    """Load all configuration from fixed-name CSV files in data_dir."""
    config = ErasureConfig(data_dir=data_dir)
    config.company = _load_company(data_dir)
    config.operators = _load_operators(data_dir)
    config.settings = _load_settings(data_dir)
    config.logo_path = _find_logo(data_dir)
    return config


def _read_csv(path: Path) -> list[dict[str, str]]:
    if not path.is_file():
        return []
    with open(path, newline="", encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def _load_company(data_dir: Path) -> CompanyInfo:
    rows = _read_csv(data_dir / "company.csv")
    if not rows:
        return CompanyInfo()
    row = rows[0]
    return CompanyInfo(
        name=row.get("name", ""),
        address=row.get("address", ""),
        phone=row.get("phone", ""),
        website=row.get("website", ""),
        email=row.get("email", ""),
    )


def _load_operators(data_dir: Path) -> list[Operator]:
    rows = _read_csv(data_dir / "operators.csv")
    return [
        Operator(
            operator_id=row.get("operator_id", ""),
            name=row.get("name", ""),
            email=row.get("email", ""),
        )
        for row in rows
    ]


def _load_settings(data_dir: Path) -> Settings:
    rows = _read_csv(data_dir / "settings.csv")
    if not rows:
        return Settings()
    row = rows[0]
    return Settings(
        default_method=row.get("default_method", "auto"),
        default_rounds=int(row.get("default_rounds", "1")),
        default_verify=row.get("default_verify", "last"),
        report_format=row.get("report_format", "pdf"),
        exclude_usb=row.get("exclude_usb", "true").lower() == "true",
    )


def _find_logo(data_dir: Path) -> Path | None:
    for ext in ("png", "jpg", "jpeg", "webp"):
        candidate = data_dir / f"logo.{ext}"
        if candidate.is_file():
            return candidate
    return None
