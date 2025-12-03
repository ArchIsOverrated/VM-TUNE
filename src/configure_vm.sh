#!/bin/bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

configure_hooks() {
  # Create hooks directory if it doesn't exist
  if [ ! -d $HOOKS_DIR ]; then
    cp -r "../hooks" "/etc/libvirt"
  fi

  if [ ! -d $VM_DIR ]; then
    mkdir -p "$VM_DIR"
    touch "$VM_DIR/allocpages.sh"
    touch "$VM_DIR/releasepages.sh"
    ln -s "$LIB_DIR/hugepages.sh" "$VM_DIR/allocpages.sh"
    ln -s "$LIB_DIR/hugepages.sh" "$VM_DIR/releasepages.sh"
  else
  fi
}

HOOKS_DIR="/etc/libvirt/hooks"
QEMU_HOOKS_DIR="$HOOKS_DIR/qemu.d"
LIB_DIR=$HOOKS_DIR/lib
VM_DIR="$QEMU_HOOKS_DIR/$1"

configure_hooks

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" >&2' ERR


