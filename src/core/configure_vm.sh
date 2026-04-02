#!/bin/bash
set -Eeuo pipefail

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./configure_vm.log >&2' ERR

########################################
# Globals
########################################

LIB_DIR=""
QUERY_MODE=""
ACTION_MODE=""

VM_NAME=""
CPU_LIST=""
EMULATOR_LIST=""
PRESET=""
IS_LAPTOP=0

HOOKS_DIR="/etc/libvirt/hooks"
QEMU_HOOKS_DIR="$HOOKS_DIR/qemu.d"
BATTERY_FILE="/var/lib/libvirt/images/fakebattery.dsl"

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
    --libdir)
      LIB_DIR="$2"
      shift 2
      ;;
    --laptop)
      IS_LAPTOP=$2
      shift 2
      ;;
    *)
      LIB_DIR="$1"
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

get_vm_list() {
  mapfile -t VMs < <(virsh list --all | tail -n+3 | awk '{print $2}' | head -n-1)
}

########################################
# Query Mode Functions
########################################

query_vms() {

  get_vm_list

  printf '{ "vms": ['

  for i in "${!VMs[@]}"; do
    printf '"%s"' "${VMs[$i]}"
    [[ $i -lt $((${#VMs[@]}-1)) ]] && printf ','
  done

  printf '] }\n'
}

query_cpu_topology() {

  CPU_VENDOR=$(detect_cpu_vendor)

  if [[ "$CPU_VENDOR" == "intel" ]]; then
    mapfile -t CORES < <(
      cat /sys/devices/system/cpu/cpu*/topology/thread_siblings_list \
      | sort -u | sort -t'-' -n
    )
  else
    mapfile -t CORES < <(
      cat /sys/devices/system/cpu/cpu*/topology/thread_siblings_list \
      | sort -u | sort -t',' -n
    )
  fi

  printf '{ "vendor":"%s", "cores":[' "$CPU_VENDOR"

  for i in "${!CORES[@]}"; do
    printf '"%s"' "${CORES[$i]}"
    [[ $i -lt $((${#CORES[@]}-1)) ]] && printf ','
  done

  printf '] }\n'
}

query_presets() {

  printf '{ "presets": ['
  printf '{ "id":1, "name":"Windows Optimized", "description":"Uses paravirtualization for best performance" },'
  printf '{ "id":2, "name":"Windows Disguised", "description":"Attempts to hide the hypervisor for malware analysis" }'
  printf '] }\n'
}

query_vm_xml_path() {

  if [[ -z "$VM_NAME" ]]; then
    echo '{"error":"vm name required"}'
    exit 1
  fi

  XML_PATH="/etc/libvirt/qemu/${VM_NAME}.xml"

  printf '{ "vm":"%s", "xml_path":"%s" }\n' "$VM_NAME" "$XML_PATH"
}

########################################
# Interactive VM Selection
########################################

chooseVM() {

  local -i index=1

  get_vm_list

  echo "Your virtual machines are:"

  for t in "${VMs[@]}"; do
    echo "$index) $t"
    ((index++))
  done

  local -i CHOSEN_VM
  read -rp "Enter a number to choose a virtual machine you would like to configure: " CHOSEN_VM

  ((CHOSEN_VM--))

  VM_NAME=${VMs[$CHOSEN_VM]}
}

########################################
# Hook Configuration
########################################

configure_hooks() {

  VM_DIR="$QEMU_HOOKS_DIR/$VM_NAME"

  if [[ ! -d "$HOOKS_DIR" ]]; then
    cp -r "$LIB_DIR/hooks" "/etc/libvirt"
  fi

  if [[ ! -d "$VM_DIR" ]]; then
    mkdir -p "$VM_DIR"
  fi

  systemctl restart libvirtd
}

########################################
# XML Configuration (Interactive)
########################################

configure_xml_interactive() {

  if ! command -v python3 >/dev/null 2>&1; then
    echo "python3 is not installed! exiting"
    exit 1
  fi

  echo
  echo "Detected CPU core layout:"

  CPU_VENDOR=$(detect_cpu_vendor)

  if [[ "$CPU_VENDOR" == "intel" ]]; then
    cat /sys/devices/system/cpu/cpu*/topology/thread_siblings_list | sort -u | sort -t'-' -n
  elif [[ "$CPU_VENDOR" == "amd" ]]; then
    cat /sys/devices/system/cpu/cpu*/topology/thread_siblings_list | sort -u | sort -t',' -n
  else
    echo "Unknown CPU vendor."
    exit 1
  fi

  echo
  read -rp "Enter comma-separated host CPU IDs to pin to: " CPU_LIST

  echo
  read -rp "Enter comma-separated emulator CPU IDs to pin to: " EMULATOR_LIST

  if [[ -f "$BATTERY_FILE" ]]; then
    read -rp "Apply asus laptop optimizations? (y/n): " IS_LAPTOP
  else
    IS_LAPTOP=0
  fi

  echo
  echo "1) Windows Optimized"
  echo "2) Windows Disguised"

  read -rp "Enter preset number: " PRESET

  configure_xml_action
}

########################################
# XML Configuration (Action Mode)
########################################

configure_xml_action() {

  XML_PATH="/etc/libvirt/qemu/${VM_NAME}.xml"
  echo "XML_PATH is $XML_PATH"

  CPU_VENDOR=$(detect_cpu_vendor)

  python3 "$LIB_DIR/src/core/configure_vm_xml.py" \
    "$XML_PATH" \
    "$CPU_LIST" \
    "$EMULATOR_LIST" \
    "$CPU_VENDOR" \
    "$IS_LAPTOP" \
    "$PRESET"

  virsh define "$XML_PATH"

  echo '{"status":"success"}'
}

########################################
# Query Dispatcher
########################################

if [[ -n "$QUERY_MODE" ]]; then

  case "$QUERY_MODE" in

    vms)
      query_vms
      ;;

    cpu-topology)
      query_cpu_topology
      ;;

    presets)
      query_presets
      ;;

    vm-xml-path)
      query_vm_xml_path
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

  if [[ $EUID -ne 0 ]]; then
    echo "Please run this script with sudo"
    exit 1
  fi

  case "$ACTION_MODE" in

    configure)

      if [[ -z "$VM_NAME" || -z "$CPU_LIST" || -z "$EMULATOR_LIST" || -z "$PRESET" ]]; then
        echo '{"error":"missing arguments"}'
        exit 1
      fi

      configure_hooks
      configure_xml_action
      ;;

    *)
      echo '{"error":"unknown action"}'
      exit 1
      ;;

  esac

  exit 0
fi

########################################
# Interactive Mode (Original Behavior)
########################################

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

chooseVM
configure_hooks
configure_xml_interactive

echo
echo "VM configuration completed for $VM_NAME"
