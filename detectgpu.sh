#!/bin/bash
set -Eeuo pipefail

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" >&2' ERR

TARGET_USER="${SUDO_USER:-$USER}"

# Constants
NVIDIA_VENDOR="0x10de"
GPU_CLASS_PREFIX="0x03"      # GPU classes: 0x03xxxx
AUDIO_CLASS_PREFIX="0x0403"  # HDMI audio classes: 0x0403xx

run_step() {
    local fail_msg="$1"
    shift
    if ! "$@"; then
        echo "$fail_msg" >&2
        exit 1
    fi
}

detect_nvidia_gpu_id() {
    local vendor_id
    local class_code
    local device_id
    local pci_address

    for device_path in /sys/bus/pci/devices/*; do

        # Only process valid PCI device entries
        if [ ! -f "$device_path/vendor" ] || \
           [ ! -f "$device_path/class" ]  || \
           [ ! -f "$device_path/device" ]; then
            continue
        fi

        vendor_id=$(cat "$device_path/vendor")   # e.g. 0x10de
        class_code=$(cat "$device_path/class")   # e.g. 0x030200

        # Skip unless vendor is NVIDIA
        if [ "$vendor_id" != "$NVIDIA_VENDOR" ]; then
            continue
        fi

        #
        # Check class prefix with substring extraction
        #

        # First 4 chars → 0x03 (GPU)
        gpu_prefix="${class_code:0:4}"

        # First 6 chars → 0x0403 (Audio)
        audio_prefix="${class_code:0:6}"

        #
        # GPU detection block
        #
        if [ "$gpu_prefix" = "$GPU_CLASS_PREFIX" ]; then
            pci_address=$(basename "$device_path")       # 0000:01:00.0
            device_id=$(cat "$device_path/device")       # e.g. 0x1f06

            GPU_PCI_ADDRESS="$pci_address"
            GPU_ID="${vendor_id#0x}:${device_id#0x}"      # remove "0x"

#            echo "Found NVIDIA GPU:"
#            echo "  PCI address = $GPU_PCI_ADDRESS"
#            echo "  ID          = $GPU_ID"

            continue
        fi

        #
        # Audio function detection block
        #
        if [ "$audio_prefix" = "$AUDIO_CLASS_PREFIX" ]; then
            pci_address=$(basename "$device_path")
            device_id=$(cat "$device_path/device")

            AUDIO_PCI_ADDRESS="$pci_address"
            AUDIO_ID="${vendor_id#0x}:${device_id#0x}"

#            echo "Found NVIDIA HDMI audio:"
#            echo "  PCI address = $AUDIO_PCI_ADDRESS"
#            echo "  ID          = $AUDIO_ID"

            continue
        fi
    done

    # Final “return value” via stdout
    if [ -n "$GPU_ID" ] && [ -n "$AUDIO_ID" ]; then
        echo "$GPU_ID,$AUDIO_ID"
        return 0
    elif [ -n "$GPU_ID" ]; then
        echo "$GPU_ID"
        return 0
    else
        # nothing found
        return 1
    fi
}

detect_nvidia_gpu_id

