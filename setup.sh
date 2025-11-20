#!/bin/bash
set -Eeuo pipefail

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" >&2' ERR

TARGET_USER="${SUDO_USER:-$USER}"

update_system() {
    echo "Starting system update..."
    run_step "System update failed." sudo dnf update -y
    echo "System update completed successfully."
}

setup_snapshots() {
    echo "Setting up automatic snapshots..."

    sudo dnf install snapper python3-dnf-plugin-snapper -y

    sudo snapper -c root create-config /

    sudo systemctl enable --now snapper-timeline.timer

    sudo systemctl enable --now snapper-cleanup.timer

    echo "Automatic snapshots setup completed successfully."
}

setup_virtualization_tools() {
    echo "Starting installation of virtualization tools..."

    sudo dnf group install --with-optional "virtualization" -y

    echo "Virtualization tools installed successfully."

    sudo systemctl enable libvirtd

    echo "libvirtd service enabled successfully."

    sudo usermod -aG libvirt "$TARGET_USER"

    echo "User $TARGET_USER added to libvirt group."
}

setup_desktop_environment() {
    echo "Starting installation of desktop environment..."

    sudo dnf install sway \
        waybar \
        pavucontrol \
        gtk-murrine-engine \
        wofi \
        network-manager-applet \
        NetworkManager-tui \
        nm-connection-editor \
        firefox \
        sddm -y

    sudo systemctl enable sddm

    sudo systemctl set-default graphical.target

    if [ ! -d "/home/$TARGET_USER/.themes" ]; then
        mkdir -p "/home/$TARGET_USER/.themes"
    fi

    cp -rf ./.themes/Gruvbox-B-MB-Dark "/home/$TARGET_USER/.themes/"

    cp ./.gtkrc-2.0 "/home/$TARGET_USER/"

    cp -rf ./.config "/home/$TARGET_USER/.config"

    sudo chown -R "$TARGET_USER:$TARGET_USER" "/home/$TARGET_USER/.themes"
    sudo chown -R "$TARGET_USER:$TARGET_USER" "/home/$TARGET_USER/.config"
    sudo chown "$TARGET_USER:$TARGET_USER" "/home/$TARGET_USER/.gtkrc-2.0"

    echo "Desktop environment installed successfully."
}

update_system
setup_snapshots
setup_virtualization_tools
setup_desktop_environment
echo "Setup completed successfully."
