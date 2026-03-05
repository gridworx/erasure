"""Tests for asset matching."""

from pathlib import Path

from erasure_ctl.core.asset_matcher import AssetMatcher


def _write_assets(tmp_path: Path, content: str) -> None:
    (tmp_path / "assets.csv").write_text(content, encoding="utf-8")


def test_match_by_system_serial(tmp_path: Path) -> None:
    _write_assets(tmp_path, (
        "system_serial,asset_tag,hostname\n"
        "5CG1234XYZ,ACME-LAP-001,alice-lap\n"
    ))
    matcher = AssetMatcher(tmp_path)
    result = matcher.match_by_system_serial("5CG1234XYZ")
    assert result is not None
    assert result.asset_tag == "ACME-LAP-001"
    assert result.hostname == "alice-lap"


def test_match_case_insensitive(tmp_path: Path) -> None:
    _write_assets(tmp_path, "system_serial\n5CG1234XYZ\n")
    matcher = AssetMatcher(tmp_path)
    assert matcher.match_by_system_serial("5cg1234xyz") is not None


def test_match_by_drive_serial(tmp_path: Path) -> None:
    _write_assets(tmp_path, (
        "system_serial,drive_serial,asset_tag\n"
        "5CG1234XYZ,WD-WMC3T0123456,ACME-LAP-001\n"
    ))
    matcher = AssetMatcher(tmp_path)
    result = matcher.match_by_drive_serial("WD-WMC3T0123456")
    assert result is not None
    assert result.system_serial == "5CG1234XYZ"


def test_no_match_returns_none(tmp_path: Path) -> None:
    _write_assets(tmp_path, "system_serial\n5CG1234XYZ\n")
    matcher = AssetMatcher(tmp_path)
    assert matcher.match_by_system_serial("NONEXISTENT") is None
    assert matcher.match_by_drive_serial("NONEXISTENT") is None


def test_unassigned_tracking(tmp_path: Path) -> None:
    _write_assets(tmp_path, (
        "system_serial,asset_tag\n"
        "AAA,ASSET-1\n"
        "BBB,ASSET-2\n"
        "CCC,ASSET-3\n"
    ))
    matcher = AssetMatcher(tmp_path)
    assert len(matcher.unassigned_assets()) == 3
    matcher.mark_assigned("AAA")
    assert len(matcher.unassigned_assets()) == 2


def test_empty_csv(tmp_path: Path) -> None:
    matcher = AssetMatcher(tmp_path)
    assert not matcher.loaded
    assert matcher.total == 0


def test_minimal_csv(tmp_path: Path) -> None:
    _write_assets(tmp_path, "system_serial,drive_serial\n5CG1234XYZ,\n")
    matcher = AssetMatcher(tmp_path)
    assert matcher.loaded
    result = matcher.match_by_system_serial("5CG1234XYZ")
    assert result is not None
    assert result.drive_serial == ""
