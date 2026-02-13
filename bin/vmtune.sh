#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./vmtune.log >&2' ERR

TARGET_USER="${SUDO_USER:-$USER}"
LIB_DIR="/usr/local/lib/"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEV_MODE=""

# parses the arguments
while getopts ":hd" opt; do
  case "$opt" in
    h)
      usage
      exit 0
      ;;
    d)
      DEV_MODE="true"
      ;;
    \?)
      error "Unknown option: -$OPTARG"
    ;;
  esac
done

if [ "$DEV_MODE" = "true" ]; then
  LIB_DIR="$SCRIPT_DIR/../src"
  echo $LIB_DIR
fi

usage() {
    echo "Usage: $0 [global options] <command> [command options]"
    echo
    echo "vm-tune: a utility to manage KVM virtual machines"
    echo
    echo "Commands:"
    echo "  configure          Run the configure wizard for your KVM VMs on libvirt"
    echo "  create             Run the create VM wizard"
    echo "  looking_glass      Install or build Looking Glass"
    echo "  passthrough        Run the GPU passthrough wizard"
    echo
    echo "Looking Glass command options:"
    echo "  -b                 Build Looking Glass"
    echo "  -i                 Install Looking Glass"
    echo
    echo "Global options:"
    echo "  -d                 Development mode (LIB_DIR points to repo instead of /usr/local/lib)"
    echo
    echo "Examples:"
    echo "  $0 looking_glass -b          Build Looking Glass"
    echo "  $0 looking_glass -i -d       Install in dev mode"
    echo "  $0 create -d                 Run create wizard in dev mode"
    exit 1
}
