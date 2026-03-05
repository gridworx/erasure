#!/bin/bash
# erasure-mount-data.sh
#
# Finds and mounts the FAT32 DATA partition from the boot USB.
# The DATA partition is identified by the label "ERASURE_DATA" or by
# being the second partition on the same device as the boot media.

set -euo pipefail

MOUNT_POINT="/mnt/erasure-data"
mkdir -p "$MOUNT_POINT"

# Strategy 1: Look for a partition with label ERASURE_DATA
LABELED=$(blkid -t LABEL="ERASURE_DATA" -o device 2>/dev/null | head -1 || true)
if [ -n "$LABELED" ]; then
    echo "Found DATA partition by label: $LABELED"
    mount -t vfat -o rw,uid=0,gid=0,umask=0022 "$LABELED" "$MOUNT_POINT"
    exit 0
fi

# Strategy 2: Find the boot device and mount its second partition
BOOT_DEV=""
for candidate in /dev/sd? /dev/nvme?n?; do
    [ -b "$candidate" ] || continue
    if grep -qs "boot=live" /proc/cmdline; then
        # In live boot, /run/live/medium is the boot source
        BOOT_SOURCE=$(findmnt -n -o SOURCE /run/live/medium 2>/dev/null || true)
        if [ -n "$BOOT_SOURCE" ]; then
            # Strip partition number to get the base device
            BOOT_DEV=$(lsblk -ndo PKNAME "$BOOT_SOURCE" 2>/dev/null || true)
            if [ -n "$BOOT_DEV" ]; then
                BOOT_DEV="/dev/$BOOT_DEV"
                break
            fi
        fi
    fi
done

if [ -n "$BOOT_DEV" ]; then
    # Look for partition 2 (or partition p2 for nvme)
    if [ -b "${BOOT_DEV}2" ]; then
        DATA_PART="${BOOT_DEV}2"
    elif [ -b "${BOOT_DEV}p2" ]; then
        DATA_PART="${BOOT_DEV}p2"
    else
        echo "WARNING: No second partition found on boot device $BOOT_DEV"
        echo "Reports will be saved to /tmp/erasure-data"
        mkdir -p /tmp/erasure-data/reports
        ln -sfn /tmp/erasure-data "$MOUNT_POINT"
        exit 0
    fi

    echo "Mounting DATA partition: $DATA_PART"
    mount -t vfat -o rw,uid=0,gid=0,umask=0022 "$DATA_PART" "$MOUNT_POINT"
    exit 0
fi

echo "WARNING: Could not find DATA partition."
echo "Reports will be saved to /tmp/erasure-data"
mkdir -p /tmp/erasure-data/reports
ln -sfn /tmp/erasure-data "$MOUNT_POINT"
