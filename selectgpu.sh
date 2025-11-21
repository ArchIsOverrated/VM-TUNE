#!/bin/bash
set -Eeuo pipefail

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" >&2' ERR

select_gpu() {
  # Get all GPU-type devices
  mapfile -t GPUS < <(lspci -nn | grep -Ei "VGA compatible controller|3D controller|Display controller")

  echo "Detected GPU devices:"
  for i in "${!GPUS[@]}"; do
    # Simple echo-based menu, 1-based index
    echo "$((i + 1))) ${GPUS[$i]}"
  done

  echo
  read -r -p "Select a GPU [1-${#GPUS[@]}]: " CHOICE

  GPU_LINE="${GPUS[$((CHOICE - 1))]}"

  # Extract PCI address (e.g. 01:00.0)
  GPU_PCI=$(awk '{print $1}' <<< "$GPU_LINE")

  # Strip the function (.0) → e.g. 01:00
  SLOT="${GPU_PCI%.*}"

  # Get all vendor:device IDs for this slot (GPU + audio, etc.)
  GPU_IDS=$(lspci -nn -s "$SLOT" \
    | grep -oE '\[[0-9a-fA-F]{4}:[0-9a-fA-F]{4}\]' \
    | tr -d '[]' \
    | paste -sd "," -)

  echo "PCI IDs for all devices on slot $SLOT:"
  echo "$GPU_IDS"
}

# Example usage:
select_gpu
# echo "Selected IDs: $GPU_IDS"

