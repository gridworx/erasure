"""Generate PDF and HTML erasure certificates."""

from __future__ import annotations

import base64
import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from erasure_ctl import __version__
from erasure_ctl.core.config import CompanyInfo

TEMPLATE_DIR = Path(__file__).parent / "templates"


@dataclass
class EvidencePhoto:
    data: str  # base64-encoded
    caption: str = ""


@dataclass
class CertificateData:
    certificate_id: str = ""
    timestamp: str = ""

    # Operator
    operator_name: str = ""
    operator_id: str = ""

    # Source system
    source_serial: str = ""
    source_asset_tag: str = ""
    source_hostname: str = ""
    source_model: str = ""
    assigned_user: str = ""
    ticket_number: str = ""

    # Disposition
    disposition_method: str = ""
    disposition_recipient: str = ""

    # Drive
    drive_serial: str = ""
    drive_model: str = ""
    drive_firmware: str = ""
    drive_capacity: str = ""
    drive_interface: str = ""

    # Erasure
    erasure_method_display: str = ""
    erasure_passes: str = ""
    verification: str = ""
    start_time: str = ""
    end_time: str = ""
    duration: str = ""
    result: str = "PASS"
    engine_version: str = ""
    erasure_system: bool = True

    # Attestation
    is_attestation: bool = False
    evidence_photos: list[EvidencePhoto] = field(default_factory=list)

    # Integrity
    sha256: str = ""


def generate_certificate_id() -> str:
    now = datetime.now(timezone.utc)
    short_uuid = uuid.uuid4().hex[:8].upper()
    return f"ERA-{now.strftime('%Y%m%d-%H%M%S')}-{short_uuid}"


def load_logo_base64(logo_path: Path | None) -> str:
    if logo_path is None or not logo_path.is_file():
        return ""
    data = logo_path.read_bytes()
    return base64.b64encode(data).decode("ascii")


def load_photo_base64(photo_path: Path, caption: str = "") -> EvidencePhoto:
    data = photo_path.read_bytes()
    encoded = base64.b64encode(data).decode("ascii")
    return EvidencePhoto(data=encoded, caption=caption or photo_path.stem)


def render_html(
    cert: CertificateData,
    company: CompanyInfo,
    logo_path: Path | None = None,
) -> str:
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATE_DIR)),
        autoescape=False,
    )
    template = env.get_template("certificate.html")
    css_path = TEMPLATE_DIR / "style.css"
    css = css_path.read_text(encoding="utf-8") if css_path.is_file() else ""

    return template.render(
        cert=cert,
        company=company,
        logo_data=load_logo_base64(logo_path),
        css=css,
        version=__version__,
    )


def compute_sha256(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


def generate_report(
    cert: CertificateData,
    company: CompanyInfo,
    logo_path: Path | None,
    output_dir: Path,
    formats: list[str] | None = None,
) -> list[Path]:
    """Generate report files and return list of created paths."""
    if formats is None:
        formats = ["pdf"]

    if not cert.certificate_id:
        cert.certificate_id = generate_certificate_id()
    if not cert.timestamp:
        cert.timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

    output_dir.mkdir(parents=True, exist_ok=True)

    filename_base = _build_filename(cert)
    created: list[Path] = []

    html_content = render_html(cert, company, logo_path)

    # Compute hash on the HTML content (which contains all the data)
    cert.sha256 = compute_sha256(html_content)
    # Re-render with hash embedded
    html_content = render_html(cert, company, logo_path)

    if "html" in formats or "both" in formats:
        html_path = output_dir / f"{filename_base}.html"
        html_path.write_text(html_content, encoding="utf-8")
        created.append(html_path)

    if "pdf" in formats or "both" in formats:
        pdf_path = output_dir / f"{filename_base}.pdf"
        _render_pdf(html_content, pdf_path)
        created.append(pdf_path)

    # Write sidecar hash
    hash_path = output_dir / f"{filename_base}.sha256"
    hash_path.write_text(
        f"{cert.sha256}  {filename_base}.pdf\n", encoding="utf-8"
    )
    created.append(hash_path)

    return created


def _build_filename(cert: CertificateData) -> str:
    date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    parts = [date]
    if cert.drive_serial:
        parts.append(cert.drive_serial)
    if cert.source_asset_tag:
        parts.append(cert.source_asset_tag)
    elif cert.source_serial:
        parts.append(cert.source_serial)
    return "_".join(parts)


def _render_pdf(html_content: str, output_path: Path) -> None:
    try:
        from weasyprint import HTML  # type: ignore[import-untyped]
        HTML(string=html_content).write_pdf(str(output_path))
    except (ImportError, OSError) as exc:
        fallback = output_path.with_suffix(".html")
        if not fallback.exists():
            fallback.write_text(html_content, encoding="utf-8")
        raise RuntimeError(
            f"PDF generation unavailable ({type(exc).__name__}). "
            f"HTML saved to {fallback}. "
            "WeasyPrint requires GTK/Pango native libraries. "
            "PDF works on Linux; on Windows use WSL or install GTK."
        ) from exc
