#!/bin/bash
# create_usb.sh — Flash the Erasure ISO to a USB stick and create the DATA partition.
#
# This script:
# 1. Writes the bootable ISO to partition 1 (ESP)
# 2. Creates a FAT32 DATA partition using the remaining space
# 3. Copies example config files to the DATA partition
#
# Usage:
#   sudo ./scripts/create_usb.sh /dev/sdX [path/to/erasure.iso]
#
# WARNING: This will DESTROY all data on the target USB device.

set -euo pipefail

DEVICE="${1:-}"
ISO="${2:-erasure.iso}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
EXAMPLE_DIR="$PROJECT_DIR/erasure-data"

if [ -z "$DEVICE" ]; then
    echo "Usage: sudo $0 /dev/sdX [path/to/erasure.iso]"
    echo ""
    echo "Available USB devices:"
    lsblk -d -o NAME,SIZE,MODEL,TRAN | grep usb || echo "  (none found)"
    exit 1
fi

if [ ! -b "$DEVICE" ]; then
    echo "Error: $DEVICE is not a block device."
    exit 1
fi

if [ "$(id -u)" -ne 0 ]; then
    echo "Error: This script must be run as root (sudo)."
    exit 1
fi

echo "============================================"
echo "  Erasure USB Creator"
echo "============================================"
echo ""
echo "  Device: $DEVICE"
echo "  ISO:    $ISO"
echo ""
echo "  WARNING: This will DESTROY all data on $DEVICE"
echo ""
read -p "  Type 'YES' to continue: " CONFIRM
if [ "$CONFIRM" != "YES" ]; then
    echo "Aborted."
    exit 1
fi

# Unmount any existing partitions
echo ""
echo "[1/5] Unmounting existing partitions..."
umount "${DEVICE}"* 2>/dev/null || true

# Write ISO to device
if [ -f "$ISO" ]; then
    echo "[2/5] Writing ISO to $DEVICE..."
    dd if="$ISO" of="$DEVICE" bs=4M status=progress conv=fsync
else
    echo "[2/5] No ISO found at $ISO — skipping ISO write."
    echo "       You can write the ISO later with: sudo dd if=erasure.iso of=$DEVICE bs=4M"
fi

# Create DATA partition in remaining space
echo "[3/5] Creating DATA partition..."
# Find the end of the last partition
LAST_END=$(parted -s "$DEVICE" unit MiB print free | grep 'Free Space' | tail -1 | awk '{print $1}')
DISK_END=$(parted -s "$DEVICE" unit MiB print free | grep 'Free Space' | tail -1 | awk '{print $2}')

if [ -n "$LAST_END" ] && [ -n "$DISK_END" ]; then
    parted -s "$DEVICE" mkpart primary fat32 "$LAST_END" "$DISK_END"
    DATA_PART="${DEVICE}2"
    # Wait for partition to appear
    sleep 2
    partprobe "$DEVICE"
    sleep 1

    echo "[4/5] Formatting DATA partition as FAT32..."
    mkfs.fat -F 32 -n ERASURE_DATA "$DATA_PART"

    echo "[5/5] Copying example config files..."
    MOUNT_POINT=$(mktemp -d)
    mount "$DATA_PART" "$MOUNT_POINT"

    cp "$EXAMPLE_DIR"/example.*.csv "$MOUNT_POINT/"
    mkdir -p "$MOUNT_POINT/reports" "$MOUNT_POINT/photos"

    echo ""
    echo "  Files on DATA partition:"
    ls -la "$MOUNT_POINT/"

    umount "$MOUNT_POINT"
    rmdir "$MOUNT_POINT"
else
    echo "[4/5] Could not determine free space — skipping DATA partition."
    echo "       Create it manually with a partition tool."
fi

echo ""
echo "============================================"
echo "  USB creation complete!"
echo ""
echo "  Next steps:"
echo "  1. Mount the DATA partition on any computer"
echo "  2. Copy example.company.csv → company.csv and fill in your info"
echo "  3. Copy example.operators.csv → operators.csv"
echo "  4. Add your logo as logo.png"
echo "  5. (Optional) Export assets.csv from your helpdesk"
echo "============================================"
