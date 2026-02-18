#!/bin/bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./setup.log >&2' ERR

TARGET_USER="${SUDO_USER:-$USER}"
DISTRO="unknown"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LIB_DIR="/usr/local/lib/VMTUNE"
INSTALL_DIR="/usr/local/bin/"

detect_distro() {
  local STRING=$(cat /etc/os-release)
  shopt -s nocasematch

  if [[ "$STRING" == *fedora* ]]; then
    echo "Fedora detected"
    DISTRO="Fedora"
  else
    echo "Supported distro not detected..."
    echo "exiting"
    DISTRO="Unknown"
    shopt -u nocasematch
    exit 1
  fi

  shopt -u nocasematch
}

update_system() {
  echo "Starting system update..."
  dnf update -y
  echo "System update completed successfully."
}

setup_snapshots() {
  echo "Setting up automatic snapshots..."

  dnf install snapper python3-dnf-plugin-snapper -y

  # Root Snapper config
  if [ ! -f /etc/snapper/configs/root ]; then
    echo "Creating Snapper config for / ..."
    snapper -c root create-config /
  else
    echo "Snapper root config already exists."
  fi

  # Home Snapper config (only works on Btrfs)
  if findmnt -n /home | grep -q "btrfs"; then
    if [ ! -f /etc/snapper/configs/home ]; then
      echo "Creating Snapper config for /home ..."
      snapper -c home create-config /home
    else
      echo "Snapper home config already exists."
    fi
  else
    echo "WARNING: /home is not on Btrfs. Skipping home Snapper config."
  fi

  # libvirt images Snapper config (ONLY when on Btrfs)
  if findmnt -n /var/lib/libvirt/images | grep -q "btrfs"; then
    if [ ! -f /etc/snapper/configs/libvirt-images ]; then
      echo "Creating Snapper config for /var/lib/libvirt/images ..."
      snapper -c libvirt-images create-config /var/lib/libvirt/images
    else
      echo "Snapper libvirt-images config already exists."
    fi
  else
    echo "NOTICE: /var/lib/libvirt/images is not on Btrfs. Snapper will not be used for it."
  fi

  # Always attempt COW disable – safe on both Btrfs and XFS
  if [ -d /var/lib/libvirt/images ]; then
    echo "Disabling COW on /var/lib/libvirt/images ..."
    if ! chattr +C /var/lib/libvirt/images; then
      echo "INFO: Could not disable COW (expected if filesystem is XFS or ext4)"
    fi
  else
    echo "WARNING: /var/lib/libvirt/images does not exist."
  fi

  systemctl enable --now snapper-timeline.timer
  systemctl enable --now snapper-cleanup.timer

  echo "Automatic snapshots setup completed successfully."
}

setup_virtualization_tools() {
  echo "Starting installation of virtualization tools..."

  dnf group install --with-optional "virtualization" -y

  echo "Virtualization tools installed successfully."

  systemctl enable --now libvirtd

  echo "libvirtd service enabled successfully."

  usermod -aG libvirt "$TARGET_USER"

  echo "User $TARGET_USER added to libvirt group."
}

setup_looking_glass() {
  if [ ! -f ./src/install_looking-glass.sh ]; then
    echo "ERROR: install_looking-glass.sh not found."
    exit 1
  fi

  echo "Running Looking Glass installer..."
  ./src/install_looking-glass.sh -bi
  echo "Looking Glass installation completed."
}

setup_VMTUNE() {
  echo "Installing the VMTUNE tool now..."

  echo "making $LIB_DIR/src folder"
  mkdir -p "$LIB_DIR/src"
  echo "making $LIB_DIR/assets folder"
  mkdir -p "$LIB_DIR/assets"
  echo "making $LIB_DIR/hooks folder"
  mkdir -p "$LIB_DIR/hooks"
  echo "copying files over to $LIB_DIR"
  cp -r "$SCRIPT_DIR/src" "$LIB_DIR/src"
  cp -r "$SCRIPT_DIR/assets" "$LIB_DIR/assets"
  cp -r "$SCRIPT_DIR/hooks" "$SCRIPT_DIR"

  echo "copying to $INSTALL_DIR"
  cp "$SCRIPT_DIR/bin/vmtune.sh" "$INSTALL_DIR"
}

setup_desktop_environment() {
  echo "Starting installation of desktop environment..."

  dnf install sway \
  waybar \
  pavucontrol \
  gtk-murrine-engine \
  wofi \
  network-manager-applet \
  NetworkManager-tui \
  nm-connection-editor \
  firefox \
  curl \
  python \
  blueman \
  kernel-tools \
  sddm -y

  #sed -i '/^installonly_limit=/d' /etc/dnf/dnf.conf
  #echo "installonly_limit=2" >> /etc/dnf/dnf.conf

  systemctl enable sddm
  systemctl enable NetworkManager

  systemctl set-default graphical.target

  if [ ! -d "/home/$TARGET_USER/.themes" ]; then
    mkdir -p "/home/$TARGET_USER/.themes"
  fi

  cp -rf ../.themes/Gruvbox-B-MB-Dark "/home/$TARGET_USER/.themes/"

  cp ../.gtkrc-2.0 "/home/$TARGET_USER/"

  cp -rf ../.config "/home/$TARGET_USER/.config"
  chown -R "$TARGET_USER:$TARGET_USER" "/home/$TARGET_USER/.themes"
  chown -R "$TARGET_USER:$TARGET_USER" "/home/$TARGET_USER/.config"
  chown "$TARGET_USER:$TARGET_USER" "/home/$TARGET_USER/.gtkrc-2.0"

  echo "Desktop environment installed successfully."
}

update_system
setup_virtualization_tools
setup_looking_glass
setup_VMTUNE

echo "Setup completed successfully."
echo "Please reboot your system to apply all changes."
