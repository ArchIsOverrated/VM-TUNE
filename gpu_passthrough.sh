#!/bin/bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" >&2' ERR

check_for_settings_file() {
  if [[ ! -f ./settings.conf ]]; then
    echo "ERROR: settings.conf not found! Creating one now..."
    cat <<EOF > ./settings.conf
# GPU Passthrough Settings
PROMPT_FOR_VFIO=1
VFIO_ENABLED=0
SELECTED_GPU_IDS=""
EOF
  fi
}

save_settings() {
  cat <<EOF > ./settings.conf
# GPU Passthrough Settings
PROMPT_FOR_VFIO=$PROMPT_FOR_VFIO
VFIO_ENABLED=$VFIO_ENABLED
SELECTED_GPU_IDS="$SELECTED_GPU_IDS"
EOF
}

select_vfio_mode() {
  read -p "Enter Passthrough mode? 1 = yes 0 = no " VFIO_ENABLED
  if [[ "$VFIO_ENABLED" != "0" && "$VFIO_ENABLED" != "1" ]]; then
    echo "Invalid input. Please enter 1 for yes or 0 for no."
    exit 1
  fi
}

select_gpu() {
  source ./settings.conf
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

  # Validate choice
  if [[ -z "$GPU_LINE" ]]; then
    echo "Invalid selection. Exiting."
    exit 1
  fi

  # Extract PCI address (e.g. 01:00.0)
  GPU_PCI=$(awk '{print $1}' <<< "$GPU_LINE")

  # Strip the function (.0) → e.g. 01:00
  SLOT="${GPU_PCI%.*}"

  # Get all vendor:device IDs for this slot (GPU + audio, etc.)
  GPU_IDS=$(lspci -nn -s "$SLOT" \
    | grep -oE '\[[0-9a-fA-F]{4}:[0-9a-fA-F]{4}\]' \
    | tr -d '[]' \
    | paste -sd "," -)

  echo "PCI IDs for all devices on slot: $SLOT"
  SELECTED_GPU_IDS="$GPU_IDS"
}

detect_cpu_vendor() {
  local vendor
  vendor=$(grep -m1 'vendor_id' /proc/cpuinfo | awk '{print $3}')

  if [[ "$vendor" == "GenuineIntel" ]]; then
    echo "intel"
  elif [[ "$vendor" == "AuthenticAMD" ]]; then
    echo "amd"
  else
    echo "unknown"
  fi
}

gpu_passthrough_setup() {
  source ./settings.conf
  local CPU_VENDOR
  CPU_VENDOR=$(detect_cpu_vendor)
  local ARGS

  if [[ "$CPU_VENDOR" == "intel" ]]; then
    echo "Detected Intel CPU. Ensuring Intel IOMMU is enabled."
    ARGS="intel_iommu=on iommu=pt rd.driver.pre=vfio-pci"
  elif [[ "$CPU_VENDOR" == "amd" ]]; then
    echo "Detected AMD CPU. Ensuring AMD IOMMU is enabled."
    ARGS="amd_iommu=on iommu=pt rd.driver.pre=vfio-pci"
  else
    echo "Unknown CPU vendor. Exiting."
    exit 1
  fi

  if [[ "$VFIO_ENABLED" -eq 1 && -n "$SELECTED_GPU_IDS" ]]; then
    echo "Configuring GPU Passthrough with VFIO for GPU IDs: $SELECTED_GPU_IDS"
    grubby --update-kernel=ALL --args="$ARGS"
    cat <<EOF > /etc/modules-load.d/vfio.conf
vfio
vfio_iommu_type1
vfio_pci
vfio_virqfd
EOF
    echo "options vfio-pci ids=$SELECTED_GPU_IDS" > /etc/modprobe.d/vfio.conf
    dracut --force
    echo "GRUB configuration updated. Please reboot for changes to take effect."
  elif [[ "$VFIO_ENABLED" -eq 0 && -n "$SELECTED_GPU_IDS" ]]; then
    echo "Removing GPU Passthrough configuration for GPU IDs: $SELECTED_GPU_IDS"
    grubby --update-kernel=ALL --remove-args="$ARGS"
    # Remove vfio module config files
    rm -f /etc/modules-load.d/vfio.conf
    rm -f /etc/modprobe.d/vfio.conf
    dracut --force
    echo "GRUB configuration reverted. Please reboot for changes to take effect."
  else
    echo "No GPU selected for passthrough. Exiting."
  fi
}

# Example usage:
check_for_settings_file

# load config after ensuring it exists
source ./settings.conf

if [[ "$PROMPT_FOR_VFIO" -eq 1 ]]; then
  select_vfio_mode
  select_gpu
  save_settings
fi

gpu_passthrough_setup
