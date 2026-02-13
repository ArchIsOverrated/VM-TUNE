#!/usr/bin/env bash
set -euo pipefail


if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./vmtune.log >&2' ERR

TARGET_USER="${SUDO_USER:-$USER}"

usage() {
  echo "Usage: $0 -b -i"
  echo
  echo "The main utility of vm-tune"
  echo
  echo "Arguments:"
  echo "  will write documentation later"
  exit 1
}

PROJECT_ROOT="/usr/local/bin"