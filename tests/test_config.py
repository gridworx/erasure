"""Tests for configuration loading."""

from pathlib import Path

from erasure_ctl.core.config import load_config


def test_load_example_config(tmp_path: Path) -> None:
    """Loading from a directory with example files should not crash."""
    config = load_config(tmp_path)
    assert config.company.name == ""
    assert config.operators == []
    assert config.settings.default_method == "auto"
    assert config.logo_path is None


def test_load_company_csv(tmp_path: Path) -> None:
    csv = tmp_path / "company.csv"
    csv.write_text('name,address,phone\nAcme Corp,"123 Main St",555-0100\n')
    config = load_config(tmp_path)
    assert config.company.name == "Acme Corp"
    assert config.company.phone == "555-0100"


def test_load_operators_csv(tmp_path: Path) -> None:
    csv = tmp_path / "operators.csv"
    csv.write_text("operator_id,name,email\nEMP-001,Alice,alice@test.com\nEMP-002,Bob,bob@test.com\n")
    config = load_config(tmp_path)
    assert len(config.operators) == 2
    assert config.operators[0].name == "Alice"
    assert config.operators[1].operator_id == "EMP-002"


def test_find_logo_png(tmp_path: Path) -> None:
    logo = tmp_path / "logo.png"
    logo.write_bytes(b"fake png data")
    config = load_config(tmp_path)
    assert config.logo_path == logo
