# Erasure

[![Build ISO](https://github.com/gridworx/erasure/actions/workflows/build-iso.yml/badge.svg)](https://github.com/gridworx/erasure/actions/workflows/build-iso.yml)
[![License: GPL v3](https://img.shields.io/badge/License-GPLv3-blue.svg)](https://www.gnu.org/licenses/gpl-3.0)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/downloads/)

**Open-source, SOC 2 compliant disk erasure with branded certificate generation.**

Erasure is a bootable Linux tool that securely wipes drives using industry-standard
methods (NIST 800-88r2, DoD 5220.22-M) and generates branded PDF/HTML certificates
with full chain-of-custody tracking. The certificate is the evidence artifact you
upload to your helpdesk or CMDB for audit compliance.

It also runs in desktop mode on any Linux or WSL workstation for wiping external
drives and generating manual attestation certificates for devices that can't boot
from USB (like Apple Silicon Macs).

---

## Features

- **Three erasure modes** — wipe internal drives (bootable), external drives (bootable or desktop), or generate manual attestation certificates
- **Auto-detected erasure method** — NVMe Crypto Erase, ATA Secure Erase, or multi-pass software overwrite depending on drive type
- **Branded PDF/HTML certificates** — company logo, operator info, drive details, NIST 800-88r2 compliance statement, SHA-256 integrity hash
- **SOC 2 CC6.5 ready** — certificates include every field auditors look for: system serial, drive serial, method, standard, result, operator, timestamp
- **CSV-driven configuration** — pre-load asset inventory from your helpdesk export; the tool auto-matches drives to source systems
- **Apple hardware support** — Intel T2 Macs boot directly; Apple Silicon Macs use the manual attestation workflow with photo evidence
- **Broad hardware support** — Debian Bookworm base with non-free firmware for NVMe, SATA, SAS, USB, and eMMC controllers
- **Terminal UI** — clean TUI built with [Textual](https://github.com/Textualize/textual), works on bare-metal consoles and terminal emulators
- **Bootable USB** — flash the ISO, add your config files to the DATA partition, boot any x86_64 machine
- **GitHub Actions CI** — push a tag, get an ISO on the Releases page

---

## How It Works

### Modes

| Mode | What it does | Where it runs |
|------|-------------|---------------|
| **Wipe This System** | Boot target machine from USB, wipe its internal drives | Bootable USB only |
| **Wipe External Drive** | Wipe drives plugged into a USB dock or cable | Bootable USB or any Linux/WSL |
| **Manual Attestation** | Generate certificate for devices erased outside the tool (Apple Silicon Macs, RMA returns, etc.) | Anywhere |

### Erasure Methods (auto-detected per drive)

| Drive Type | Default Method | Approximate Time |
|-----------|---------------|-----------------|
| NVMe SSD | Crypto Erase via `nvme-cli` (hardware) | ~2 seconds |
| SATA SSD | ATA Secure Erase via `hdparm` (hardware) | ~30 sec – 2 min |
| HDD | DoD Short 3-pass via `nwipe` (software) | ~30 min / TB |
| Apple SSD | Not supported directly — use macOS "Erase All Content and Settings" + Manual Attestation | ~5 min |

All methods meet or exceed **NIST 800-88r2 Purge** level.

### What's on the Certificate

- Company logo and info
- Source system serial number (the join key to your helpdesk asset)
- Drive serial, model, capacity
- Erasure method, standard reference (NIST 800-88r2), pass/fail with verification
- Operator name, date, duration
- SHA-256 integrity hash of the certificate itself
- Photo evidence (manual attestation mode)
- Additional asset info from your CSV (hostname, assigned user, disposition method, ticket number)

---

## Installation

### Option A: Bootable USB (recommended for production)

1. Download `erasure-<version>-amd64.iso` from [Releases](https://github.com/gridworx/erasure/releases)
2. Flash to USB with [Rufus](https://rufus.ie) (Windows) or `dd` (Linux):

```bash
sudo dd if=erasure-*.iso of=/dev/sdX bs=4M status=progress
```

3. Create a second partition on the USB for your config files and reports:
   - Use `scripts/create_usb.sh` on Linux, or manually create a FAT32 partition labeled `ERASURE_DATA` in the remaining space

4. Copy your config files to the DATA partition (see [Setup](#setup) below)

### Option B: Install from Source (desktop mode)

```bash
git clone https://github.com/gridworx/erasure.git
cd erasure
pip install -e ".[dev]"
```

Requires Python 3.10+. For PDF generation, you also need GTK/Pango/Cairo libraries
(`sudo apt install libpango-1.0-0 libpangocairo-1.0-0 libcairo2 libgdk-pixbuf-2.0-0`
on Debian/Ubuntu). Without them, HTML reports are generated instead.

### Option C: Download a Binary (desktop mode, no Python needed)

Download from [Releases](https://github.com/gridworx/erasure/releases):
- `erasure-ctl-linux` — Linux desktop mode
- `erasure-ctl-windows.exe` — Windows desktop mode (WSL recommended for drive access)

---

## Setup

All configuration lives as simple CSV files on the USB DATA partition or in a local
`erasure-data/` folder. Copy the example files, rename them, and fill in your info.
This takes about 5 minutes.

### 1. Company Info

```bash
cp erasure-data/example.company.csv erasure-data/company.csv
```

```csv
name,address,phone,website,email
Your Company,"123 Main St, City, ST 12345",+1 555-0100,https://yourcompany.com,it@yourcompany.com
```

### 2. Operators

```bash
cp erasure-data/example.operators.csv erasure-data/operators.csv
```

```csv
operator_id,name,email
EMP-001,Alice Johnson,alice@yourcompany.com
EMP-002,Bob Williams,bob@yourcompany.com
```

### 3. Asset Inventory (optional but recommended)

```bash
cp erasure-data/example.assets.csv erasure-data/assets.csv
```

Export from your helpdesk or CMDB. Only `system_serial` is strictly required for
compliance — everything else is optional enrichment since your helpdesk asset
record already has the details:

```csv
system_serial,asset_tag,hostname,system_model,assigned_user,drive_serial,disposition_method,ticket_number
5CG1234XYZ,YOURCO-LAP-001,alice-lap,HP EliteBook 840 G8,Alice Johnson,WD-WMC3T0123456,Donation,HD-1001
```

### 4. Logo

Drop your company logo as `erasure-data/logo.png` (or `.jpg`).

### 5. Settings (optional)

```bash
cp erasure-data/example.settings.csv erasure-data/settings.csv
```

```csv
default_method,default_rounds,default_verify,report_format,exclude_usb
auto,1,last,pdf,true
```

---

## Usage

### Desktop Mode (external drives + manual attestation)

```bash
# Wipe external drives (needs root for disk access)
sudo erasure-ctl --data-dir ./erasure-data/

# Manual attestation only (no root needed)
erasure-ctl --data-dir ./erasure-data/

# WSL on Windows
wsl erasure-ctl --data-dir /mnt/c/Users/you/erasure-data/

# Development with mock drives
erasure-ctl --mock --data-dir ./erasure-data/
```

### Bootable Mode (internal + external + attestation)

1. Plug USB into target machine
2. Boot from USB (change boot order or press F12/Esc at POST)
3. Select your name from the operator list
4. Choose a mode: **Wipe This System**, **External Drive**, or **Manual Attestation**
5. Review auto-detected info, confirm, wipe
6. Save report, reboot, next machine

### Apple Silicon Macs (manual attestation workflow)

Apple Silicon Macs cannot boot external Linux. Instead:

1. On each Mac: **Settings > General > Transfer or Reset > Erase All Content and Settings**
2. Take photos: "About This Mac" screen, erase confirmation dialog, post-erase setup assistant
3. On any workstation: run `erasure-ctl`, select **Manual Attestation**
4. Enter the serial number (auto-fills from `assets.csv` if present), attach photos
5. Generate certificate and upload to helpdesk

### Intel T2 MacBooks

Works with the bootable USB, but requires a one-time pre-step per machine:

1. Boot macOS Recovery (Cmd+R)
2. Utilities > Startup Security Utility
3. Set Secure Boot to **No Security**
4. Enable **Allow booting from external or removable media**
5. Reboot, hold Option, select the Erasure USB

---

## File Layout

```
erasure-data/                          (on USB DATA partition or local folder)
├── company.csv                        Your company info
├── operators.csv                      Authorized operators
├── assets.csv                         Asset inventory (optional)
├── settings.csv                       Preferences (optional)
├── logo.png                           Company logo
│
├── results.csv                        Auto-generated cumulative wipe log
└── reports/
    ├── 2026-03-05_WD-WMC3T0123456_ACME-LAP-001.pdf
    ├── 2026-03-05_WD-WMC3T0123456_ACME-LAP-001.html
    └── 2026-03-05_WD-WMC3T0123456_ACME-LAP-001.sha256
```

---

## SOC 2 Compliance

This tool produces evidence for **SOC 2 CC6.5** (logical and physical asset
disposition). Each certificate contains the fields auditors require:

| Field | Purpose |
|-------|---------|
| System serial number | Ties the certificate to your CMDB asset record |
| Drive serial number | Proves which specific media was sanitized |
| Erasure method + NIST 800-88r2 | Proves an accepted standard was followed |
| Pass/fail with verification | Proves it actually worked |
| Operator identity + timestamp | Proves who did it and when |
| SHA-256 hash | Tamper evidence on the certificate itself |

Upload the PDF to the asset in your helpdesk. The auditor sees the certificate
on the asset record. Done.

---

## Building the Bootable ISO

The ISO is built automatically by GitHub Actions on every tag push. You can also
build it locally on any Debian/Ubuntu machine (or WSL2).

### Automated (GitHub Actions)

1. Push a tag:

```bash
git tag v0.1.0
git push origin v0.1.0
```

2. GitHub Actions builds the ISO (~15 minutes)
3. Download it from the [Releases](https://github.com/gridworx/erasure/releases) page

The workflow can also be triggered manually from the **Actions** tab.

### Local Build (Debian/Ubuntu or WSL2)

```bash
sudo apt-get install live-build

cd iso/
sudo bash build.sh
# Output: iso/erasure-<version>-amd64.iso
```

### What's in the ISO

- Debian Bookworm (minimal, no desktop environment)
- Linux kernel with all storage controller modules
- Non-free firmware (Intel, Realtek, Broadcom, Atheros, QLogic)
- `nwipe`, `nvme-cli`, `hdparm`, `smartmontools`, `dmidecode`
- Python 3 + Textual + WeasyPrint + Jinja2
- `erasure-ctl` pre-installed and auto-launched on boot
- GRUB bootloader (UEFI + Legacy BIOS)

Estimated ISO size: ~800 MB – 1.2 GB.

### Boot Flow

```
USB Stick
  └─> GRUB Bootloader
        └─> Linux Kernel + initramfs
              └─> live-boot (loads squashfs into RAM)
                    └─> systemd
                          ├─> Mount USB DATA partition at /mnt/erasure-data
                          └─> Launch erasure-ctl TUI on tty1
```

### Testing the ISO Locally

Before flashing to physical hardware, test in a VM:

**QEMU (quick, headless-friendly):**

```bash
# Create a dummy disk to wipe
qemu-img create -f qcow2 test-disk.qcow2 1G

# Boot the ISO with UEFI firmware
qemu-system-x86_64 \
    -m 2048 \
    -cdrom iso/erasure-*-amd64.iso \
    -drive file=test-disk.qcow2,format=qcow2 \
    -boot d \
    -enable-kvm \
    -bios /usr/share/ovmf/OVMF.fd
```

Install OVMF for UEFI: `sudo apt install ovmf`

**VirtualBox:**

1. Create a new VM (Type: Linux, Version: Debian 64-bit)
2. Allocate at least 2 GB RAM
3. Add a small virtual hard disk (1–2 GB) to act as the wipe target
4. Mount the ISO as a virtual optical disk
5. Under **System > Motherboard**, enable EFI
6. Boot the VM — the Erasure TUI should auto-launch

**What to verify:**

- GRUB menu appears with "Erasure — Secure Disk Wipe Tool"
- TUI launches automatically after boot
- Virtual disk is detected in the drive list
- A wipe can be initiated and completes successfully
- Reports are generated (check `/mnt/erasure-data/reports/` or `/tmp/erasure-data/reports/`)

---

## Development

```bash
# Clone the repo
git clone https://github.com/gridworx/erasure.git
cd erasure

# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest

# Run with mock data (no real drives)
erasure-ctl --mock --data-dir ./erasure-data/

# Generate sample reports
python scripts/generate_sample_report.py

# Build standalone binary
pip install pyinstaller
pyinstaller --onefile --name erasure-ctl erasure_ctl/__main__.py
```

### Project Structure

```
erasure/
├── erasure_ctl/                  Python package
│   ├── __main__.py               CLI entry point
│   ├── core/
│   │   ├── runtime.py            Bootable vs. desktop mode detection
│   │   ├── config.py             CSV config loader
│   │   ├── asset_matcher.py      Asset inventory matching
│   │   ├── dmi.py                System info from DMI/SMBIOS
│   │   └── discovery.py          Block device discovery + capability detection
│   ├── reports/
│   │   ├── generator.py          HTML/PDF report generation
│   │   └── templates/
│   │       ├── certificate.html  Jinja2 certificate template
│   │       └── style.css         Certificate styling
│   └── tui/
│       └── app.py                Textual TUI application
├── erasure-data/                 Example config files
│   ├── example.company.csv
│   ├── example.operators.csv
│   ├── example.assets.csv
│   └── example.settings.csv
├── iso/                          Bootable ISO build system
│   ├── build.sh                  Main build script (calls live-build)
│   └── config/
│       ├── package-lists/        Debian packages to include
│       ├── hooks/live/           Build-time hooks (install erasure-ctl)
│       ├── includes.chroot/      Files baked into the live filesystem
│       └── bootloaders/          Custom GRUB configuration
├── scripts/
│   ├── generate_sample_report.py
│   ├── build_binary.py
│   └── create_usb.sh            USB flashing + DATA partition helper
├── .github/workflows/
│   └── build-iso.yml             GitHub Actions ISO build
├── pyproject.toml
└── README.md
```

---

## Contributing

Contributions are welcome. Please open an issue first to discuss what you'd like
to change, especially for larger features.

1. Fork the repo
2. Create a feature branch (`git checkout -b feature/my-change`)
3. Make your changes
4. Run `pytest` to verify nothing is broken
5. Open a pull request

---

## Acknowledgements

- [nwipe](https://github.com/martijnvanbrummelen/nwipe) — disk wiping engine
- [nvme-cli](https://github.com/linux-nvme/nvme-cli) — NVMe management
- [hdparm](https://sourceforge.net/projects/hdparm/) — ATA drive commands
- [Textual](https://github.com/Textualize/textual) — terminal UI framework
- [WeasyPrint](https://weasyprint.org/) — HTML to PDF rendering
- [Debian live-build](https://live-team.pages.debian.net/live-manual/) — ISO build system

---

## License

[GPL-3.0-or-later](https://www.gnu.org/licenses/gpl-3.0.html)
