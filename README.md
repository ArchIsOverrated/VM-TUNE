# CustomFedora

This repository contains a small collection of helper scripts I use to build and
configure a custom Fedora VM environment (GPU passthrough, VM creation and a
helper to download Looking Glass artifacts). The README documents what each
script does and how to run them safely.

**Overview**
- **Purpose:** provide scripts to create VMs, enable GPU passthrough and fetch
	Looking Glass source artifacts easily.
- **Location:** repository root contains the main scripts referenced below.

**Files**
- **`configurevm.sh`**: Will give you options to configure your virtual machines. Not made yet
- **`createvm.sh`**: helper to create and configure a VM (see script header
	for usage). Behavior depends on your system configuration.
- **`gpu_passthrough.sh`**: configures VFIO for GPU passthrough and updates
	kernel boot args.
- **`setup.sh`**: general setup helper for initial system configuration. It assumes you are using fedora as your distro and then installs and configures sway as a lightweight desktop to be used as the hypervisor environment. It also sets up QEMU/KVM
with Virt-Manager frontend. Check Fedora Documentation for more information.
- **`download_looking-glass.sh`**: small downloader that defaults to
	`https://looking-glass.io/artifact/stable/source`, preserving the filename the
	server supplies (uses `curl` with `-J` or falls back to `wget`).
- **`install_looking-glass.sh`**: installer for Looking Glass (if present) —
	read the script header for options.


**Warning**
Do not run the virtual machine in the BTRFS file system it may be significantly more laggy