#!/bin/bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" >&2' ERR

select_os_variant() {
  echo "Select VM type:"
  echo "  1) Windows 11 gaming VM"
  echo "  2) Windows 10 gaming VM"
  echo "  3) Linux VM"
  read -r -p "Enter choice [1]: " CHOICE
  CHOICE=${CHOICE:-1}

  case "$CHOICE" in
  1)
    OS_VARIANT="win11"
    ;;
  2)
    OS_VARIANT="win10"
    ;;
  3)
    OS_VARIANT=""
    ;;
  4)
    OS_VARIANT="generic"
    ;;
    esac
}

select_vm_name() {
  read -r -p "Enter VM name: " VM_NAME
  if [[ -z "$VM_NAME" ]]; then
      echo "VM name cannot be empty. Exiting."
      exit 1
  fi
}

select_iso_path() {
  read -r -p "Enter path to OS installation ISO: " ISO_PATH
  if [[ ! -f "$ISO_PATH" ]]; then
    echo "ISO file not found at $ISO_PATH. Exiting."
    exit 1
  fi

  REAL_USER="${SUDO_USER:-$USER}"

  USER_HOME=$(getent passwd "$REAL_USER" | awk -F: '{print $6}')

  if [[ -n "$USER_HOME" && "$ISO_PATH" == "$USER_HOME/"* ]]; then
    HOME_PERMS=$(stat -c '%A' "$USER_HOME")

    GROUP_PERMS=${HOME_PERMS:4:3}

    if [[ "$GROUP_PERMS" != *x* ]]; then
      echo
      echo "The ISO is inside $USER_HOME."
      echo "QEMU needs group 'execute' permission on this directory to reach the ISO."
      echo "Fixing it by running:"
      echo "  chmod g+x \"$USER_HOME\""
      echo
      chmod +x "$USER_HOME"
      fi
  fi
}

select_disk_size() {
  read -r -p "Enter disk size for VM (e.g., 40, but assume in GiB): " DISK_SIZE
  if [[ -z "$DISK_SIZE" ]]; then
    echo "Disk size cannot be empty. Exiting."
    exit 1
  fi
}

select_ram_size() {
  read -r -p "Enter RAM size for VM in MB (e.g., 8192): " RAM_SIZE
  if [[ -z "$RAM_SIZE" ]]; then
    echo "RAM size cannot be empty. Exiting."
    exit 1
  fi
}

select_cpu_count() {
  read -r -p "Enter number of CPU cores for the VM (e.g., 4): " CPU_COUNT
  if [[ -z "$CPU_COUNT" ]]; then
    echo "CPU count cannot be empty. Exiting."
    exit 1
  fi
}

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

  echo "VM '$VM_NAME' created. It should now be visible in virt-manager."
}

select_os_variant
select_vm_name
select_iso_path
select_disk_size
select_ram_size
select_cpu_count
create_vm

