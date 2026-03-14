#!/bin/bash
set -Eeuo pipefail

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./install_looking-glass.log >&2' ERR

TARGET_USER="${SUDO_USER:-$USER}"

QUERY_MODE=""
ACTION_MODE=""

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
    *)
      shift
      ;;
  esac
done

########################################
# Query Functions
########################################

query_status() {

  if command -v looking-glass >/dev/null 2>&1; then
    STATUS="installed"
  else
    STATUS="not_installed"
  fi

  printf '{ "looking_glass":"%s" }\n' "$STATUS"
}

query_build_exists() {

  if compgen -G "looking-glass-*/client/build/looking-glass-client" > /dev/null; then
    RESULT=true
  else
    RESULT=false
  fi

  printf '{ "build_exists":%s }\n' "$RESULT"
}

query_dependencies() {

  printf '{ "dependencies": ['

  printf '"cmake","gcc","gcc-c++","libglvnd-devel","fontconfig-devel",'
  printf '"spice-protocol","make","nettle-devel","pkgconf-pkg-config",'
  printf '"binutils-devel","wayland-devel","wayland-protocols-devel",'
  printf '"libxkbcommon-devel","dejavu-sans-mono-fonts","libdecor-devel",'
  printf '"pipewire-devel","libsamplerate-devel"'

  printf '] }\n'
}

########################################
# Build Function
########################################

build_looking_glass() {
  echo "Starting installation of Looking Glass..."
  dnf install -y \
    cmake gcc gcc-c++ \
    libglvnd-devel fontconfig-devel \
    spice-protocol make nettle-devel \
    pkgconf-pkg-config binutils-devel \
    wayland-devel wayland-protocols-devel \
    libxkbcommon-devel \
    dejavu-sans-mono-fonts \
    libdecor-devel \
    pipewire-devel libsamplerate-devel

    URL="https://looking-glass.io/artifact/stable/source"
    OUT="looking-glass.tar.gz"

    # Check if already exists
    if [[ ! -f "$OUT" ]]; then
      echo "Downloading Looking Glass..."
    	curl -L "$URL" -o "$OUT"
    fi

    # Check non-empty
    if [[ ! -s "$OUT" ]]; then
        echo "ERROR: Download failed, file is empty."
        exit 1
    fi

    # Checks to see if gzip compressed archive
    if ! file "$OUT" | grep -q "gzip compressed data"; then
        echo "ERROR: File is not a valid gzip archive."
        exit 1
    fi

    # Extract folder name safely
    EXTRACTED_DIR=$(ls looking-glass* | head -1)

    # Extract if folder doesn't exist
    if [[ ! -d "$EXTRACTED_DIR" ]]; then
        echo "Extracting Looking Glass..."
        tar -xzf "$OUT"
    fi

    #checks to see if it was already built if not then build
    if ! compgen -G "looking-glass-*/client/build/looking-glass-client" > /dev/null; then
      
      cd looking-glass*/

      mkdir -p ./client/build

      cd ./client/build

      cmake ../ \
        -DENABLE_X11=OFF \
        -DENABLE_WAYLAND=ON \
        -DENABLE_PIPEWIRE=ON \
        -DENABLE_PULSEAUDIO=OFF

      make
      
      cd ../../../
    fi
}

########################################
# Install Function
########################################

install_looking_glass() {

  echo "Configuring Looking Glass..."

  sudo bash -c "cat > /etc/tmpfiles.d/10-looking-glass.conf <<EOF
# Type Path               Mode UID  GID Age Argument
f /dev/shm/looking-glass 0660 $TARGET_USER qemu -
EOF"

  if sudo semanage fcontext -l | grep -q "^/dev/shm/looking-glass"; then
    sudo semanage fcontext -m -t svirt_tmpfs_t /dev/shm/looking-glass
  else
    sudo semanage fcontext -a -t svirt_tmpfs_t /dev/shm/looking-glass
  fi

  cp looking-glass-*/client/build/looking-glass-client /usr/local/bin/looking-glass

  echo "Looking Glass installation completed."
}

########################################
# Cleanup
########################################

cleanup_looking_glass() {

  echo "Performing cleanup"
  rm -rf looking-glass*
  echo "Cleanup complete"
}

########################################
# Query Dispatcher
########################################

if [[ -n "$QUERY_MODE" ]]; then

  case "$QUERY_MODE" in
    status)
      query_status
      ;;
    build-exists)
      query_build_exists
      ;;
    dependencies)
      query_dependencies
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

    build)
      build_looking_glass
      echo '{"status":"built"}'
      ;;

    install)
      install_looking_glass
      echo '{"status":"installed"}'
      ;;

    cleanup)
      cleanup_looking_glass
      echo '{"status":"cleaned"}'
      ;;

    full-install)
      build_looking_glass
      install_looking_glass
      cleanup_looking_glass
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
  echo "Please run with sudo"
  exit 1
fi

echo "Looking Glass Installer"
echo "1) Build"
echo "2) Install"
echo "3) Full Install"

read -rp "Select option: " CHOICE

case "$CHOICE" in
  1)
    build_looking_glass
    ;;
  2)
    install_looking_glass
    cleanup_looking_glass
    ;;
  3)
    build_looking_glass
    install_looking_glass
    cleanup_looking_glass
    ;;
  *)
    echo "Invalid option"
    ;;
esac
