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
    echo "  -d                 Development mode (LIB_DIR points to repo instead of /usr/local/lib)"
    echo
    echo "Examples:"
    echo "  $0 looking_glass -b          Build Looking Glass"
    echo "  $0 looking_glass -i -d       Install in dev mode"
    exit 1
}

parse_args() {

    # --- Parse global options ---
    while [[ "$1" == -* ]]; do
        case "$1" in
            -d) DEV_MODE=1 ;;
            *) echo "Unknown global option: $1"; usage ;;
        esac
        shift
    done

    # --- Subcommand ---
    cmd="$1"
    shift || true

    case "$cmd" in
        configure)
            echo "Running configure wizard (DEV_MODE=$DEV_MODE)"
            ;;
        create)
            echo "Running create wizard (DEV_MODE=$DEV_MODE)"
            ;;
        looking_glass)
            BUILD=0
            INSTALL=0
            while getopts "bi" opt; do
                case "$opt" in
                    b) BUILD=1 ;;
                    i) INSTALL=1 ;;
                    \?) echo "Invalid option for looking_glass: -$OPTARG"; usage ;;
                esac
            done
            shift $((OPTIND-1))
            echo "Looking Glass options: BUILD=$BUILD INSTALL=$INSTALL DEV_MODE=$DEV_MODE"
            ;;
        passthrough)
            echo "Running passthrough wizard (DEV_MODE=$DEV_MODE)"
            ;;
        *)
            echo "Unknown command: $cmd"
            usage
            ;;
    esac
}

parse_args $@
# parses the arguments
# if -d set devmode to true

if [[ "$DEV_MODE" = "1" ]]; then
  LIB_DIR="$SCRIPT_DIR/../src"
  echo $LIB_DIR
fi

