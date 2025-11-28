#!/bin/bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" >&2' ERR

TARGET_USER="${SUDO_USER:-$USER}"

update_system() {
  echo "Starting system update..."
  dnf update -y
  echo "System update completed successfully."
}

setup_snapshots() {
  echo "Setting up automatic snapshots..."

  dnf install snapper python3-dnf-plugin-snapper -y

  snapper -c root create-config /

  if findmnt -n /home | grep -q "btrfs"; then
    echo "Creating Snapper config for /home ..."
    snapper -c home create-config /home
  else
    echo "WARNING: /home is not on Btrfs or not a subvolume. Skipping home Snapper config."
  fi

  systemctl enable --now snapper-timeline.timer

  systemctl enable --now snapper-cleanup.timer

  echo "Automatic snapshots setup completed successfully."
}

setup_virtualization_tools() {
  echo "Starting installation of virtualization tools..."

  dnf group install --with-optional "virtualization" -y

  echo "Virtualization tools installed successfully."

  systemctl enable libvirtd

  echo "libvirtd service enabled successfully."

  usermod -aG libvirt "$TARGET_USER"

  echo "User $TARGET_USER added to libvirt group."
}

setup_looking-glass() {
  ./install_looking-glass.sh
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
  sddm -y

  systemctl enable sddm

  systemctl set-default graphical.target

  if [ ! -d "/home/$TARGET_USER/.themes" ]; then
    mkdir -p "/home/$TARGET_USER/.themes"
  fi

  cp -rf ./.themes/Gruvbox-B-MB-Dark "/home/$TARGET_USER/.themes/"

  cp ./.gtkrc-2.0 "/home/$TARGET_USER/"

  cp -rf ./.config "/home/$TARGET_USER/.config"

  chown -R "$TARGET_USER:$TARGET_USER" "/home/$TARGET_USER/.themes"
  chown -R "$TARGET_USER:$TARGET_USER" "/home/$TARGET_USER/.config"
  chown "$TARGET_USER:$TARGET_USER" "/home/$TARGET_USER/.gtkrc-2.0"

  echo "Desktop environment installed successfully."
}

update_system
setup_snapshots
setup_virtualization_tools
setup_desktop_environment
echo "Setup completed successfully."
