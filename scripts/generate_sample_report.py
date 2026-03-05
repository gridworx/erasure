#!/usr/bin/env python3
"""Generate a sample report to verify templates work."""

from pathlib import Path

from erasure_ctl.core.config import CompanyInfo
from erasure_ctl.reports.generator import (
    CertificateData,
    generate_report,
)

OUTPUT_DIR = Path(__file__).parent.parent / "erasure-data" / "reports"
DATA_DIR = Path(__file__).parent.parent / "erasure-data"


def main() -> None:
    company = CompanyInfo(
        name="Acme Corporation",
        address="123 Main Street, Suite 400, Edmonton, AB T5J 1N9",
        phone="+1 (780) 555-0100",
        website="https://acme-corp.example.com",
        email="it@acme-corp.example.com",
    )

    logo_path = DATA_DIR / "logo.png"
    if not logo_path.is_file():
        logo_path = None

    cert = CertificateData(
        operator_name="Alice Johnson",
        operator_id="EMP-001",
        source_serial="5CG1234XYZ",
        source_asset_tag="ACME-LAP-001",
        source_hostname="ajohnson-lap",
        source_model="HP EliteBook 840 G8",
        assigned_user="Alice Johnson",
        ticket_number="HD-1001",
        disposition_method="Donation",
        disposition_recipient="Free Geek Edmonton",
        drive_serial="WD-WMC3T0123456",
        drive_model="WDC WD10EZEX-08WN4A0",
        drive_firmware="01.01A01",
        drive_capacity="1,000,204,886,016 bytes (1.00 TB)",
        drive_interface="SATA 6.0 Gb/s",
        erasure_method_display="DoD 5220.22-M Short (3-pass)",
        erasure_passes="3",
        verification="Last pass verified",
        start_time="2026-03-05 14:30:22 UTC",
        end_time="2026-03-05 16:45:18 UTC",
        duration="2h 14m 56s",
        result="PASS",
        engine_version="nwipe 0.40",
    )

    print("Generating sample report...")
    try:
        files = generate_report(
            cert, company, logo_path, OUTPUT_DIR,
            formats=["html", "pdf"],
        )
    except RuntimeError as e:
        print(f"  Note: {e}")
        files = generate_report(
            cert, company, logo_path, OUTPUT_DIR,
            formats=["html"],
        )
    for f in files:
        print(f"  Created: {f}")

    # Also generate a manual attestation sample
    att_cert = CertificateData(
        operator_name="Alice Johnson",
        operator_id="EMP-001",
        source_serial="C02X1234ABCD",
        source_asset_tag="ACME-LAP-004",
        source_hostname="cmartinez-mbp",
        source_model="MacBook Pro 14\" M2 2023",
        assigned_user="Carol Martinez",
        ticket_number="HD-1004",
        disposition_method="Donation",
        disposition_recipient="Free Geek Edmonton",
        drive_serial="APPLE SSD AP0512Q",
        drive_model="Apple SSD AP0512Q",
        drive_capacity="512 GB",
        drive_interface="NVMe (Apple Silicon — soldered)",
        erasure_method_display="macOS EACAS — Cryptographic Erase",
        result="PASS",
        is_attestation=True,
    )

    print("\nGenerating manual attestation sample...")
    try:
        att_files = generate_report(
            att_cert, company, logo_path, OUTPUT_DIR,
            formats=["html", "pdf"],
        )
    except RuntimeError:
        att_files = generate_report(
            att_cert, company, logo_path, OUTPUT_DIR,
            formats=["html"],
        )
    for f in att_files:
        print(f"  Created: {f}")

    print("\nDone! Check erasure-data/reports/")


if __name__ == "__main__":
    main()
