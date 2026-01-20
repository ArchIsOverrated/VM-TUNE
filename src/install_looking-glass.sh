#!/bin/bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./install_looking-glass.log >&2' ERR

TARGET_USER="${SUDO_USER:-$USER}"

build_looking-glass() {
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

    echo "Downloading Looking Glass..."
    curl -L "$URL" -o "$OUT"

    # Check non-empty
    if [[ ! -s "$OUT" ]]; then
        echo "ERROR: Download failed, file is empty."
        exit 1
    fi

    if ! file "$OUT" | grep -q "gzip compressed data"; then
        echo "ERROR: File is not a valid gzip archive."
        exit 1
    fi

    echo "Extracting Looking Glass..."
    tar -xzf "$OUT"
    cd looking-glass-*/
    
    mkdir -p client/build
    cd client/build
    cmake ../ \
      -DENABLE_X11=OFF \
      -DENABLE_WAYLAND=ON \
      -DENABLE_PIPEWIRE=ON \
      -DENABLE_PULSEAUDIO=OFF

    make
}

configure_looking-glass() {
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
  if ! grep -q 'alias looking-glass="/home/'"$TARGET_USER"'/CustomFedora/src/looking-glass-B7/client/build/looking-glass-client"' \
      "/home/$TARGET_USER/.bashrc"; then
    echo 'alias looking-glass="/home/'"$TARGET_USER"'/CustomFedora/src/looking-glass-B7/client/build/looking-glass-client"' \
      >> "/home/$TARGET_USER/.bashrc"
  fi
  echo "Looking Glass installation completed."
}

setup_looking-glass() {
  build_looking-glass
  configure_looking-glass
}
setup_looking-glass
build_looking-glass
