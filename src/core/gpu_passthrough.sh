#!/bin/bash
set -Eeuo pipefail

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./gpu_passthrough.log >&2' ERR

########################################
# Globals
########################################

QUERY_MODE=""
ACTION_MODE=""

VFIO_ENABLED=""
SELECTED_GPU_IDS=""
GPU_SLOT=""

########################################
# Argument Parsing
########################################

while [[ $# -gt 0 ]]; do
  case "$1" in
    --query)
      QUERY_MODE="$2"
      shift 2
      ;;
    --action)
      ACTION_MODE="$2"
      shift 2
      ;;
    --vfio)
      VFIO_ENABLED="$2"
      shift 2
      ;;
    --gpuids)
      SELECTED_GPU_IDS="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

########################################
# Helpers
########################################

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

########################################
# Query Functions
########################################

query_gpus() {

  mapfile -t GPUS < <(
    lspci -nn | grep -Ei "VGA compatible controller|3D controller|Display controller"
  )

  printf '{ "gpus": ['

  for i in "${!GPUS[@]}"; do

    GPU_LINE="${GPUS[$i]}"
    PCI=$(awk '{print $1}' <<< "$GPU_LINE")

    SLOT="${PCI%.*}"

    IDS=$(lspci -nn -s "$SLOT" \
      | grep -oE '\[[0-9a-fA-F]{4}:[0-9a-fA-F]{4}\]' \
      | tr -d '[]' \
      | paste -sd "," -)

    printf '{'
    printf '"name":"%s",' "$GPU_LINE"
    printf '"pci":"%s",' "$PCI"
    printf '"ids":"%s"' "$IDS"
    printf '}'

    [[ $i -lt $((${#GPUS[@]}-1)) ]] && printf ','

  done

  printf '] }\n'
}

query_cpu_vendor() {

  CPU_VENDOR=$(detect_cpu_vendor)

  printf '{ "cpu_vendor":"%s" }\n' "$CPU_VENDOR"
}

query_iommu_status() {

  CMDLINE=$(cat /proc/cmdline)

  if grep -qE "intel_iommu=on|amd_iommu=on" <<< "$CMDLINE"; then
    STATUS="enabled"
  else
    STATUS="disabled"
  fi

  printf '{ "iommu":"%s" }\n' "$STATUS"
}

########################################
# Interactive Functions
########################################

select_vfio_mode() {

  read -p "Enter Passthrough mode? 1 = yes 0 = no: " VFIO_ENABLED

  if [[ "$VFIO_ENABLED" != "0" && "$VFIO_ENABLED" != "1" ]]; then
    echo "Invalid input."
    exit 1
  fi
}

select_gpu() {

  mapfile -t GPUS < <(
    lspci -nn | grep -Ei "VGA compatible controller|3D controller|Display controller"
  )

  echo "Detected GPU devices:"

  for i in "${!GPUS[@]}"; do
    echo "$((i + 1))) ${GPUS[$i]}"
  done

  read -r -p "Select a GPU [1-${#GPUS[@]}]: " CHOICE

  GPU_LINE="${GPUS[$((CHOICE - 1))]}"

  if [[ -z "$GPU_LINE" ]]; then
    echo "Invalid selection."
    exit 1
  fi

  GPU_PCI=$(awk '{print $1}' <<< "$GPU_LINE")

  SLOT="${GPU_PCI%.*}"

  GPU_IDS=$(lspci -nn -s "$SLOT" \
    | grep -oE '\[[0-9a-fA-F]{4}:[0-9a-fA-F]{4}\]' \
    | tr -d '[]' \
    | paste -sd "," -)

  SELECTED_GPU_IDS="$GPU_IDS"
}

########################################
# GPU Passthrough Setup
########################################

gpu_passthrough_setup() {

  if [[ $EUID -ne 0 ]]; then
    echo "Run with sudo."
    exit 1
  fi

  CPU_VENDOR=$(detect_cpu_vendor)

  if [[ "$CPU_VENDOR" == "intel" ]]; then
    ARGS="intel_iommu=on iommu=pt rd.driver.pre=vfio-pci"
  elif [[ "$CPU_VENDOR" == "amd" ]]; then
    ARGS="amd_iommu=on iommu=pt rd.driver.pre=vfio-pci"
  else
    echo "Unknown CPU vendor."
    exit 1
  fi

  if [[ "$VFIO_ENABLED" -eq 1 ]]; then

    grubby --update-kernel=ALL --args="$ARGS"

    cat <<EOF > /etc/modules-load.d/vfio.conf
vfio
vfio_iommu_type1
vfio_pci
vfio_virqfd
EOF

    echo "options vfio-pci ids=$SELECTED_GPU_IDS" > /etc/modprobe.d/vfio.conf

    dracut --force -v

    echo "GPU passthrough enabled."

  else

    grubby --update-kernel=ALL --remove-args="$ARGS"

    rm -f /etc/modules-load.d/vfio.conf
    rm -f /etc/modprobe.d/vfio.conf

    dracut --force -v

    echo "GPU passthrough disabled."

  fi
}

########################################
# Query Dispatcher
########################################

if [[ -n "$QUERY_MODE" ]]; then

  case "$QUERY_MODE" in

    gpus)
      query_gpus
      ;;

    cpu-vendor)
      query_cpu_vendor
      ;;

    iommu-status)
      query_iommu_status
      ;;

    *)
      echo '{"error":"unknown query"}'
      exit 1
      ;;

  esac

  exit 0
fi

########################################
# Action Dispatcher
########################################

if [[ -n "$ACTION_MODE" ]]; then

  case "$ACTION_MODE" in

    set)

      if [[ -z "$VFIO_ENABLED" || -z "$SELECTED_GPU_IDS" ]]; then
        echo '{"error":"missing arguments"}'
        exit 1
      fi

      gpu_passthrough_setup

      echo '{"status":"success"}'
      ;;

    *)
      echo '{"error":"unknown action"}'
      exit 1
      ;;

  esac

  exit 0
fi

########################################
# Interactive Mode
########################################

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

select_vfio_mode
select_gpu

gpu_passthrough_setup
