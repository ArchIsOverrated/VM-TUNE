#!/bin/bash
set -Eeuo pipefail

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./createvm.log >&2' ERR

########################################
# Globals
########################################

QUERY_MODE=""
ACTION_MODE=""

VM_NAME=""
ISO_PATH=""
DISK_SIZE=""
RAM_SIZE=""
CPU_COUNT=""
OS_VARIANT=""

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
    --iso)
      ISO_PATH="$2"
      shift 2
      ;;
    --disk)
      DISK_SIZE="$2"
      shift 2
      ;;
    --ram)
      RAM_SIZE="$2"
      shift 2
      ;;
    --cpu)
      CPU_COUNT="$2"
      shift 2
      ;;
    --osvariant)
      OS_VARIANT="$2"
      shift 2
      ;;
    *)
      shift
      ;;
  esac
done

########################################
# Query Functions
########################################

query_isos() {

  mapfile -t ISOS < <(
    find /var/lib/libvirt/images /home /mnt /media \
      -type f -iname "*.iso" 2>/dev/null
  )

  printf '{ "isos": ['

  for i in "${!ISOS[@]}"; do
    printf '"%s"' "${ISOS[$i]}"
    [[ $i -lt $((${#ISOS[@]}-1)) ]] && printf ','
  done

  printf '] }\n'
}

query_os_variants() {

  mapfile -t VARIANTS < <(osinfo-query os --fields short-id | tail -n +2)

  printf '{ "os_variants": ['

  for i in "${!VARIANTS[@]}"; do
    printf '"%s"' "${VARIANTS[$i]}"
    [[ $i -lt $((${#VARIANTS[@]}-1)) ]] && printf ','
  done

  printf '] }\n'
}

query_defaults() {

  printf '{'
  printf '"default_ram":4096,'
  printf '"default_cpu":2,'
  printf '"default_disk":40'
  printf '}\n'
}

########################################
# Interactive Functions
########################################

select_iso_path() {


  REAL_USER="${SUDO_USER:-$USER}"

  USER_HOME=$(getent passwd "$REAL_USER" | awk -F: '{print $6}')

  if [[ -n "$USER_HOME" && "$ISO_PATH" == "$USER_HOME/"* ]]; then

    HOME_PERMS=$(stat -c '%A' "$USER_HOME")

    GROUP_PERMS=${HOME_PERMS:4:3}

    if [[ "$GROUP_PERMS" != *x* ]]; then
      chmod +x "$USER_HOME"
    fi
  fi
}

select_disk_size() {

  read -r -p "Enter disk size for VM (GiB): " DISK_SIZE

  if [[ -z "$DISK_SIZE" ]]; then
    echo "Disk size cannot be empty."
    exit 1
  fi
}

select_ram_size() {

  read -r -p "Enter RAM size for VM in MB: " RAM_SIZE

  if [[ -z "$RAM_SIZE" ]]; then
    echo "RAM size cannot be empty."
    exit 1
  fi
}

select_cpu_count() {

  read -r -p "Enter number of CPU cores: " CPU_COUNT

  if [[ -z "$CPU_COUNT" ]]; then
    echo "CPU count cannot be empty."
    exit 1
  fi
}

########################################
# VM Creation
########################################

create_vm() {

  echo "Creating VM '$VM_NAME'..."

  if [[ -n "$OS_VARIANT" ]]; then

    virt-install \
      --name "$VM_NAME" \
      --ram "$RAM_SIZE" \
      --vcpus "$CPU_COUNT" \
      --disk size="$DISK_SIZE",format=qcow2 \
      --cdrom "$ISO_PATH" \
      --os-variant "$OS_VARIANT" \
      --noautoconsole

  else

    virt-install \
      --name "$VM_NAME" \
      --ram "$RAM_SIZE" \
      --vcpus "$CPU_COUNT" \
      --disk size="$DISK_SIZE",format=qcow2 \
      --cdrom "$ISO_PATH" \
      --noautoconsole

  fi

  echo "VM '$VM_NAME' created."
}

########################################
# Query Dispatcher
########################################

if [[ -n "$QUERY_MODE" ]]; then

  case "$QUERY_MODE" in

    isos)
      query_isos
      ;;

    os-variants)
      query_os_variants
      ;;

    defaults)
      query_defaults
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
    echo "Run with sudo."
    exit 1
  fi

  case "$ACTION_MODE" in

    create)

      if [[ -z "$VM_NAME" || -z "$ISO_PATH" || -z "$RAM_SIZE" || -z "$CPU_COUNT" || -z "$DISK_SIZE" ]]; then
        echo '{"error":"missing arguments"}'
        exit 1
      fi

      select_iso_path
      create_vm

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

read -rp "Enter VM name: " VM_NAME

read -rp "Enter ISO path: " ISO_PATH
select_iso_path
select_disk_size
select_ram_size
select_cpu_count

create_vm
