#!/bin/bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./install_looking-glass.log >&2' ERR

TARGET_USER="${SUDO_USER:-$USER}"

usage() {
  echo "Usage: $0 -b -i"
  echo
  echo "This script will build and install looking-glass on your system."
  echo
  echo "Arguments:"
  echo "  -b will build looking-glass for you."
  echo "  -i will install looking-glass to /usr/local/bin"
  exit 1
}

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

cleanup_looking_glass() {
  echo "Performing cleanup tasks"
  rm -rf looking-glass*
  echo "Cleanup done. Looking-glass is now installed"
}

# parses the arguments
while getopts ":hbi" opt; do
  case "$opt" in
    h)
      usage
      exit 0
      ;;
    b)
      build_looking_glass
      ;;
    i)
      install_looking_glass
      cleanup_looking_glass
      ;;
    \?)
      error "Unknown option: -$OPTARG"
    ;;
  esac
done



