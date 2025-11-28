#!/bin/bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" >&2' ERR


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

setup_looking-glass() {
  build_looking-glass
}
setup_looking-glass
