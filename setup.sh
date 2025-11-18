#!/bin/bash
set -euo pipefail

TARGET_USER="${SUDO_USER:-$USER}"

update_system() {
    echo "Starting system update..."
    sudo dnf update -y
    if [ $? -ne 0 ]; then
        echo "System update failed."
        exit 1
    fi
    echo "System update completed successfully."
}

setup_virtualization_tools() {
    echo "Starting installation of virtualization tools..."
    sudo dnf group install --with-optional "virtualization" -y
    if [ $? -ne 0 ]; then
        echo "Installation of virtualization tools failed."
        exit 1
    fi
    echo "Virtualization tools installed successfully."

    sudo systemctl enable libvirtd
        if [ $? -ne 0 ]; then
            echo "Enabling libvirtd service failed."
            exit 1
        fi
        echo "libvirtd service enabled successfully."

    sudo usermod -aG libvirt $TARGET_USER
    if [ $? -ne 0 ]; then
        echo "Adding user to libvirt group failed."
        exit 1
    fi
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
    if [ $? -ne 0 ]; then
        echo "Installation of desktop packages failed"
        exit 1
    fi

    sudo systemctl enable sddm
    if [ $? -ne 0 ]; then
        echo "Enabling SDDM failed."
        exit 1
    fi

    sudo systemctl set-default graphical.target
    if [ $? -ne 0 ]; then
        echo "Setting default target to graphical failed."
        exit 1
    fi

    if [ ! -d "/home/$TARGET_USER/.themes" ]; then
        mkdir -p "/home/$TARGET_USER/.themes"
    fi

    cp -rf ./.themes/Gruvbox-B-MB-Dark "/home/$TARGET_USER/.themes/"
    if [ $? -ne 0 ]; then
       echo "Copying theme failed"
       exit 1
    fi

    cp ./.gtkrc-2.0 "/home/$TARGET_USER/"
    cp -rf ./.config "/home/$TARGET_USER/.config"
    if [ $? -ne 0 ]; then
       echo "Copying config files failed"
       exit 1
    fi

    sudo chown -R $TARGET_USER:$TARGET_USER "/home/$TARGET_USER/.themes"
    sudo chown -R $TARGET_USER:$TARGET_USER "/home/$TARGET_USER/.config"
    sudo chown $TARGET_USER:$TARGET_USER "/home/$TARGET_USER/.gtkrc-2.0"

    echo "Desktop environment installed successfully."
}

update_system
setup_virtualization_tools
setup_desktop_environment
