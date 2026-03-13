#!/bin/bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./configure_vm.log >&2' ERR
usage() {
  echo "Usage:"
  echo "  configure_vm.sh --libdir PATH [options]"
  echo
  echo "Options:"
  echo "  --json             Enable JSON API mode"
  echo "  --vm NAME          VM name"
  echo "  --cpu LIST         CPU pin list"
  echo "  --emulator LIST    Emulator CPU list"
  echo "  --preset NUM       Preset number"
  echo "  --laptop BOOL      Laptop optimizations"
  echo
  exit 0
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

configure_hooks() {
  # Create hooks directory if needed
  if [[ ! -d "$HOOKS_DIR" ]]; then
    cp -r "$LIB_DIR/hooks" "/etc/libvirt"
  fi

  # Create per-VM directory
  if [[ ! -d "$VM_DIR" ]]; then
    mkdir -p "$VM_DIR"
  fi

  systemctl restart libvirtd
}

configure_xml() {
  CPU_VENDOR=$(detect_cpu_vendor)
  python3 "$LIB_DIR/src/core/configure_vm_xml.py" "$XML_PATH" "$CPU_LIST" "$EMULATOR_LIST" "$CPU_VENDOR" "$IS_LAPTOP" "$PRESET"

  virsh define "$XML_PATH"
}

json_output() {
  if [[ $JSON_MODE -eq 1 ]]; then
    printf '%s\n' "$1"
  fi
}

json_error() {
  if [[ $JSON_MODE -eq 1 ]]; then
    printf '{"status":"error","message":"%s"}\n' "$1"
  else
    echo "$1"
  fi
  exit 1
}

JSON_MODE=0
API_MODE=0

LIB_DIR=""
VM_NAME=""
CPU_LIST=""
EMULATOR_LIST=""
PRESET=""
IS_LAPTOP=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --libdir)
      LIB_DIR="$2"
      shift 2
      ;;

    --json)
      JSON_MODE=1
      API_MODE=1
      shift
      ;;

    --vm)
      VM_NAME="$2"
      shift 2
      ;;

    --cpu)
      CPU_LIST="$2"
      shift 2
      ;;

    --emulator)
      EMULATOR_LIST="$2"
      shift 2
      ;;

    --preset)
      PRESET="$2"
      shift 2
      ;;

    --laptop)
      IS_LAPTOP="$2"
      shift 2
      ;;

    -h|--help)
      usage
      ;;

    *)
      echo "Unknown argument: $1"
      exit 1
      ;;
  esac
done

echo "DEBUG: LIBDIR is $LIB_DIR"
echo "DEBUG: VM_NAME is $VM_NAME"
echo "DEBUG: CPU_LIST is $CPU_LIST"
echo "DEBUG: EMULATOR_LIST is $EMULATOR_LIST"
echo "DEBUG: PRESET is $PRESET"
echo "DEBUG: IS_LAPTOP is $IS_LAPTOP"

HOOKS_DIR="/etc/libvirt/hooks"
QEMU_HOOKS_DIR="$HOOKS_DIR/qemu.d"
VM_DIR="$QEMU_HOOKS_DIR/$VM_NAME"
BATTERY_FILE="/var/lib/libvirt/images/fakebattery.dsl"
XML_PATH="/etc/libvirt/qemu/${VM_NAME}.xml"

configure_hooks
configure_xml

