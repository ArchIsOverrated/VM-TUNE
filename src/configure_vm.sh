#!/bin/bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" >&2' ERR

usage() {
  echo "Usage: $0 <vm-name>"
  echo
  echo "This script configures libvirt hooks for the specified VM."
  echo
  echo "Arguments:"
  echo "  vm-name    The name of the virtual machine to configure hooks for."
  exit 1
}

configure_hooks() {
  # Create hooks directory if it doesn't exist
  if [ ! -d $HOOKS_DIR ]; then
    cp -r "../hooks" "/etc/libvirt"
  fi

  if [ ! -d $VM_DIR ]; then
    mkdir -p "$VM_DIR"
    ln -s "$LIB_DIR/hugepages.sh" "$VM_DIR/allocpages.sh"
    ln -s "$LIB_DIR/hugepages.sh" "$VM_DIR/releasepages.sh"
  fi
}

if [[ "${1:-}" == "-h" || $# -lt 1 ]]; then
  usage
fi

HOOKS_DIR="/etc/libvirt/hooks"
QEMU_HOOKS_DIR="$HOOKS_DIR/qemu.d"
LIB_DIR=$HOOKS_DIR/lib
VM_DIR="$QEMU_HOOKS_DIR/$1"

configure_hooks
