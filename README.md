# VM-TUNE

This repository contains a small collection of helper scripts I use to build and
configure a custom Fedora VM environment (GPU passthrough, VM creation and a
helper to download Looking Glass artifacts). The README documents what each
script does and how to run them safely.

**Overview**
- **Purpose:** provide scripts to create VMs, enable GPU passthrough and fetch
	Looking Glass source artifacts easily.
- **Location:** repository root contains the main scripts referenced below.

**Setup and main files**
- **`setup.sh`**: general setup helper for initial system configuration. It assumes you are using fedora as your distro and then installs and configures sway as a lightweight desktop to be used as the hypervisor environment. It also sets up QEMU/KVM
with Virt-Manager frontend. It will also set up a single CLI tool for you to use vmtune.sh you can run "sudo vmtune.sh -h" for more details on how to use this" Check Fedora Documentation for more information.
- **`bin/vmtune.sh`**: this is the main script that will act as the main interface that people will interact with, when running the setup.sh script, it will be installed to /usr/local/bin/vmtune.sh and you can run "sudo vmtune.sh -h" for more details regarding to use this.
- **`bin/vmtune`**: this is the wrapper for the main script with polkit policy and rules applied for it so that if you are in the libvirt group you do not need to run the script with sudo. It's just a wrapper that says "pkexec vmtune. USE THIS SCRIPT FOR INTERACING

**Supporting scripts**
So these scripts here aren't really the main scripts you will interface with. These will act as supporting scripts that the vmtune tool will call in the background and after running the setup script they will be installed to /usr/local/lib/VMTUNE where the script vmtune script located at /usr/local/bin/vmtune.sh will call
- **`src/configurevm.sh`**: Will give you options to configure your virtual machines. So far it sets up the libvirt hooks for the virtual machines. It configures HUGEPAGES and CPU isolation but you must have CPU pinning and have the huge pages tag in your xml config fo this to work. There is some limited functionality for this script editing the virtual machine XML for you such as adding the huge pages and a guided setup for cpu pinning.
- **`src/createvm.sh`**: helper to create and configure a VM (see script header
	for usage). Behavior depends on your system configuration.
- **`src/gpu_passthrough.sh`**: configures VFIO for GPU passthrough and updates
	kernel boot args.
- **`src/install_looking-glass.sh`**: Downloads and compiles looking-glass from source

**Libvirt Hooks**
- **`qemu`**: This is the dispatcher script for the hooking scripts that will enable hugepages and isolating cpu when starting the VM. It will also undo the huge pages and cpu isolation on VM shutoff. It should work if you configure cpu pinning and hugepages in the xml config. It might work if you only have huge pages but do not have cpu pinning but I haven't tested it so I cannot say.
- **`lib/hugepages.sh`**: This hook will be configured to be called for you if you setup configure vm script. It will change teh VM from running on 4KiB pages to 2MiB pages which greatly increases VM performance. You must configure your VM to have at least 2MiB and your virtual machine memory ram allocation must be a multiple of 2 or else the script will have an error.
- **`lib/isolatecpus.sh`**: You must have cpu pinning configured in your xml for this to work. This isolates SYSTEMD processes from the VM cores so that the VM cores don't experience as much noise from the Linux Kernel.
- **`lib/performancegoverner.sh`**: This sets the cpu performance governor to performance when you start your virtual machine for maximum performance and likewise back to powersaving when you quit your virtual machine"

**Config files**
- **`polkit/50-vmtune.rules`**: This is a file that is installed to /usr/share/polkit-1/rules.d/ that defines how to apply the vmtune policy. It says if you are in the libvirt group then allow them to connect to the virtual machines using the policy.
- **`polkit/vmtune.policy`**: For this file applies the actual policy that 50-vmtune.rules applies.

**How you can contribute**
You can contribute by refining this documentation or adding new features or adding support for other distros on this since this script only supports RHEL based systems like Fedora.

**Warning**
Do not run the virtual machine in the BTRFS file system it may be significantly more laggy
