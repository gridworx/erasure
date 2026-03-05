#!/bin/bash
# build.sh — Build the Erasure bootable ISO using Debian live-build.
#
# This script configures and builds a Debian Bookworm live ISO containing
# nwipe, nvme-cli, hdparm, Python + erasure-ctl, and broad hardware firmware.
#
# Requirements: Debian/Ubuntu host with live-build installed.
#   sudo apt-get install live-build
#
# Usage:
#   cd iso/
#   sudo ./build.sh
#
# Output: live-image-amd64.hybrid.iso

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

cd "$SCRIPT_DIR"

echo "============================================"
echo "  Erasure ISO Builder"
echo "============================================"
echo ""

# Clean any previous build
if [ -d ".build" ] || [ -d "chroot" ]; then
    echo "[1/4] Cleaning previous build..."
    lb clean --purge 2>/dev/null || true
fi

echo "[2/4] Configuring live-build..."

lb config \
    --binary-image iso-hybrid \
    --distribution bookworm \
    --archive-areas "main contrib non-free non-free-firmware" \
    --architectures amd64 \
    --linux-packages "linux-image" \
    --linux-flavours "amd64" \
    --binary-filesystem fat32 \
    --firmware-binary true \
    --firmware-chroot true \
    --memtest none \
    --win32-loader false \
    --iso-application "Erasure" \
    --iso-publisher "Erasure Project" \
    --iso-volume "ERASURE" \
    --bootappend-live "boot=live components quiet splash timezone=UTC" \
    --apt-indices false \
    --apt-recommends false \
    --cache true

# Copy our Python package into the chroot so the hook can install it
echo "[3/4] Staging erasure-ctl source for chroot installation..."
mkdir -p config/includes.chroot/opt/erasure-ctl-src
cp -r "$PROJECT_ROOT/erasure_ctl" config/includes.chroot/opt/erasure-ctl-src/
cp "$PROJECT_ROOT/pyproject.toml" config/includes.chroot/opt/erasure-ctl-src/
cp "$PROJECT_ROOT/README.md" config/includes.chroot/opt/erasure-ctl-src/

echo "[4/4] Building ISO (this takes 10-20 minutes)..."
lb build

# Rename output for clarity
ISO_FILE=$(ls -1 live-image-amd64.hybrid.iso 2>/dev/null || true)
if [ -n "$ISO_FILE" ]; then
    VERSION=$(grep -oP 'version = "\K[^"]+' "$PROJECT_ROOT/pyproject.toml" || echo "dev")
    OUTPUT_NAME="erasure-${VERSION}-amd64.iso"
    mv "$ISO_FILE" "$OUTPUT_NAME"
    echo ""
    echo "============================================"
    echo "  ISO built successfully!"
    echo "  Output: iso/$OUTPUT_NAME"
    SIZE=$(du -h "$OUTPUT_NAME" | cut -f1)
    echo "  Size:   $SIZE"
    echo "============================================"
else
    echo "ERROR: ISO file not found. Check build logs above."
    exit 1
fi
