#!/usr/bin/env bash
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./vmtune.log >&2' ERR

TARGET_USER="${SUDO_USER:-$USER}"
LIB_DIR="/usr/local/lib/VMTUNE"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEV_MODE="false"

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
    echo "  -d                 Development mode (LIB_DIR points to repo instead of /usr/local/lib/VMTUNE)"
    echo
    echo "Examples:"
    echo "  $0 looking_glass -b          Build Looking Glass"
    echo "  $0 looking_glass -i -d       Install in dev mode"
    exit 1
}

parse_args() {
    if [[ $# == 0 ]]; then
        echo "no arguments provided"
        usage
    fi
    # --- Parse global options ---
    while [[ "${1:-}" == -* ]]; do
        case "$1" in
            -d)
                DEV_MODE=1
                LIB_DIR="$SCRIPT_DIR/../"
                echo "LIB_DIR = $LIB_DIR"
                ;;
            *)
                echo "Unknown global option: $1"
                usage
                ;;
        esac
        shift
    done

    # --- Subcommand ---
    cmd="$1"
    shift || true

    case "$cmd" in
        configure)
            echo "executing configure_vm.sh"
            "$LIB_DIR/src/configure_vm.sh" "$LIB_DIR"
            ;;
        create)
            echo "executing createvm.sh"
            "$LIB_DIR/src/createvm.sh"
            ;;
        looking_glass)
            BUILD=""
            INSTALL=""
            while getopts "bi" opt; do
                case "$opt" in
                    b) BUILD="-b" ;;
                    i) INSTALL="-i" ;;
                    \?) echo "Invalid option for looking_glass: -$OPTARG"; usage ;;
                esac
            done
            shift $((OPTIND-1))
            echo "Looking Glass options: BUILD=$BUILD INSTALL=$INSTALL DEV_MODE=$DEV_MODE"
            "$LIB_DIR/src/install_looking-glass.sh" "$BUILD" "$INSTALL"
            ;;
        passthrough)
            echo "Running passthrough wizard (DEV_MODE=$DEV_MODE)"
            "$LIB_DIR/src/gpu_passthrough.sh"
            ;;
        *)
            echo "Unknown command: $cmd"
            usage
            ;;
    esac
}

# parses the arguments
parse_args $@
