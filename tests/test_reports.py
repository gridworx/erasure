"""Tests for report generation."""

from pathlib import Path

from erasure_ctl.core.config import CompanyInfo
from erasure_ctl.reports.generator import (
    CertificateData,
    generate_certificate_id,
    generate_report,
    render_html,
)


def test_certificate_id_format() -> None:
    cert_id = generate_certificate_id()
    assert cert_id.startswith("ERA-")
    parts = cert_id.split("-")
    assert len(parts) == 4


def test_render_html_minimal() -> None:
    cert = CertificateData(
        certificate_id="ERA-TEST-001",
        drive_serial="WD-TEST123",
        erasure_method_display="DoD Short (3-pass)",
        result="PASS",
    )
    company = CompanyInfo(name="Test Corp")
    html = render_html(cert, company)
    assert "ERA-TEST-001" in html
    assert "WD-TEST123" in html
    assert "Test Corp" in html
    assert "PASS" in html


def test_render_html_with_source_system() -> None:
    cert = CertificateData(
        certificate_id="ERA-TEST-002",
        source_serial="5CG1234XYZ",
        source_asset_tag="ACME-LAP-001",
        source_hostname="alice-lap",
        drive_serial="WD-TEST123",
        erasure_method_display="NVMe Crypto Erase",
        result="PASS",
    )
    company = CompanyInfo(name="Acme Corp")
    html = render_html(cert, company)
    assert "5CG1234XYZ" in html
    assert "ACME-LAP-001" in html
    assert "alice-lap" in html


def test_render_html_attestation() -> None:
    cert = CertificateData(
        certificate_id="ERA-TEST-003",
        drive_serial="APPLE-SSD-123",
        erasure_method_display="macOS EACAS — Cryptographic Erase",
        is_attestation=True,
        result="PASS",
    )
    company = CompanyInfo(name="Test Corp")
    html = render_html(cert, company)
    assert "Manual Attestation" in html
    assert "outside the Erasure tool" in html


def test_generate_report_html(tmp_path: Path) -> None:
    cert = CertificateData(
        drive_serial="WD-TEST123",
        source_serial="SYS-001",
        erasure_method_display="Zero Fill",
        result="PASS",
    )
    company = CompanyInfo(name="Test Corp")
    files = generate_report(cert, company, None, tmp_path, formats=["html"])
    html_files = [f for f in files if f.suffix == ".html"]
    assert len(html_files) == 1
    content = html_files[0].read_text(encoding="utf-8")
    assert "WD-TEST123" in content
    assert cert.sha256 != ""
