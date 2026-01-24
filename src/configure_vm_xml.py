#!/usr/bin/env python3
import sys
import xml.etree.ElementTree as ET
import hashlib
import data

if len(sys.argv) != 7:
    print("Usage: configure_xml.py <xml-path> <cpu-list> <emulator-cpu-list> <cpu-vendor> <is-laptop> <preset>")
    sys.exit(1)

xml_path = sys.argv[1]
cpu_list_str = sys.argv[2]
emulator_list = sys.argv[3]
cpu_vendor = sys.argv[4]
is_laptop = sys.argv[5]
preset = sys.argv[6]
print(xml_path)
print(cpu_list_str)
print(emulator_list)
print(cpu_vendor)
print(is_laptop)
print(preset)

preset_options = ["WindowsOptimized","WindowsDisguised","LinuxOptimized","LinuxDisguised"]
virtual_machine_preset = preset_options[int(preset)-1]

cpus = [c.strip() for c in cpu_list_str.split(",") if c.strip()]

tree = ET.parse(xml_path)
root = tree.getroot()

def deterministic_random(data, clamp):
    h = hashlib.sha256(data.encode("utf-8")).digest()
    value = int.from_bytes(h,"big")
    return value % clamp

# -----------------------------
# Add <memoryBacking><hugepages/>
# -----------------------------
def huge_pages():
    memoryBacking = root.find("memoryBacking")
    if memoryBacking is None:
        memoryBacking = ET.SubElement(root, "memoryBacking")

    # Remove existing children if any
    for child in memoryBacking.findall("*"):
        memoryBacking.remove(child)

    ET.SubElement(memoryBacking, "hugepages")

# -----------------------------
# CPU layout
# -----------------------------
def cpu_layout():
    cpu = root.find("cpu")
    if cpu is None:
        print("Error: your xml is broken there is no cpu defined!")
        sys.exit(1)

    # Remove existing topology (idempotent)
    for topo in cpu.findall("topology"):
        cpu.remove(topo)

    # Remove existing topoext feature (idempotent)
    for feat in cpu.findall("feature"):
        if feat.get("name") == "topoext":
            cpu.remove(feat)

    # Calculate topology
    total_vcpus = len(cpus)
    threads = 2
    cores = total_vcpus // threads

    topology = ET.SubElement(cpu, "topology", {
        "sockets": "1",
        "dies": "1",
        "clusters": "1",
        "cores": str(cores),
        "threads": str(threads),
    })

    # AMD-only topoext
    if cpu_vendor.lower() == "amd":
        ET.SubElement(cpu, "feature", {
            "policy": "require",
            "name": "topoext"
        })
    
# -----------------------------
# CPU pinning
# -----------------------------
def cpu_pinning():
    cputune = root.find("cputune")
    if cputune is None:
        cputune = ET.SubElement(root, "cputune")

    # Remove previous pins
    for pin in list(cputune.findall("vcpupin")):
        cputune.remove(pin)

    # Remove previous emulator pins
    for pin in list(cputune.findall("emulatorpin")):
        cputune.remove(pin)

    vcpu_elem = root.find("vcpu")

    if vcpu_elem is None or not vcpu_elem.text:
        print("Error: no <vcpu> element found")
        sys.exit(1)

    num_vcpus = int(vcpu_elem.text)

    # Only pin what the user gave
    for v in range(min(num_vcpus, len(cpus))):
        ET.SubElement(cputune, "vcpupin", {"vcpu": str(v), "cpuset": cpus[v]})
    ET.SubElement(cputune, "emulatorpin", {"cpuset": emulator_list})

def scsi():
    # Find <devices>
    devices = root.find("devices")
    if devices is None:
        print("Error: no <devices> element found")
        sys.exit(1)

    # Remove existing NVMe controllers
    for controller in list(devices.findall("controller")):
        if controller.get("type") == "scsi":
            devices.remove(controller)

    # Add NVMe controller
    ET.SubElement(devices, "controller", {"type": "scsi", "index": "0", "model": "virtio-scsi"})

    # Find the first real disk in the VM
    disk = None
    for d in devices.findall("disk"):
        if d.get("device") == "disk":
            disk = d
            break

    if disk is None:
        print("Error: no <disk device='disk'> found")
        sys.exit(1)

     # Ensure <driver> exists and set performance-friendly options
    driver = disk.find("driver")
    if driver is None:
        driver = ET.SubElement(disk, "driver")   

    driver.set("name", "qemu")
    driver.set("type", "qcow2")
    driver.set("cache", "none")
    driver.set("io", "native")
    driver.set("discard", "unmap")

    # Ensure <target> exists and set NVMe target
    target = disk.find("target")
    if target is None:
        target = ET.SubElement(disk, "target")

    target.set("dev", "sda")
    target.set("bus", "scsi")
    target.set("rotation_rate", "1")

    # Remove drive-style address (SATA/SCSI) if present; NVMe is PCIe
    for addr in list(disk.findall("address")):
        if addr.get("type") == "drive":
            disk.remove(addr)

    # Create/update <serial> (libvirt requires serial for NVMe)
    uuid_elem = root.find("uuid")
    if uuid_elem is None or uuid_elem.text is None or uuid_elem.text.strip() == "":
        print("Error: no <uuid> found (virt-install normally creates this)")
        sys.exit(1)

    vm_uuid = uuid_elem.text.strip()
    digest = hashlib.sha256(vm_uuid.encode("utf-8")).hexdigest()
    serial_value = "S5G" + digest[0:17]  # 20 chars total

    serial = disk.find("serial")
    if serial is None:
        serial = ET.SubElement(disk, "serial")
    serial.text = serial_value

    number_ssd_brands = len(data.ssd_models)
    chosen_model = data.ssd_models[deterministic_random(vm_uuid,number_ssd_brands)]
    chosen_vendor = chosen_model.get("vendor")
    products = chosen_model.get("models")
    number_of_products = len(products)
    chosen_product = products[deterministic_random(vm_uuid,number_of_products)]

    vendor = disk.find("vendor")
    if vendor is None:
      vendor = ET.SubElement(disk, "vendor")
    vendor.text = chosen_vendor 

    product = disk.find("product")
    if product is None:
      product = ET.SubElement(disk, "product")
    product.text = chosen_product 

# -----------------------------
# NVME emulation
# -----------------------------
def nvme_emulation():
    # Find <devices>
    devices = root.find("devices")
    if devices is None:
        print("Error: no <devices> element found")
        sys.exit(1)

    # Remove existing NVMe controllers
    for controller in list(devices.findall("controller")):
        if controller.get("type") == "nvme":
            devices.remove(controller)

    # Get VM UUID (used for serials)
    uuid_elem = root.find("uuid")
    if uuid_elem is None or not uuid_elem.text or uuid_elem.text.strip() == "":
        print("Error: no <uuid> found (virt-install normally creates this)")
        sys.exit(1)

    vm_uuid = uuid_elem.text.strip()

    # Find all real disks
    disk_elements = []
    for disk_element in devices.findall("disk"):
        if disk_element.get("device") == "disk":
            disk_elements.append(disk_element)

    if not disk_elements:
        print("Error: no <disk device='disk'> found")
        sys.exit(1)

    # Process each disk
    for disk_index, disk_element in enumerate(disk_elements):
        # Add one NVMe controller per disk
        ET.SubElement(
            devices,
            "controller",
            {
                "type": "nvme",
                "index": str(disk_index),
            },
        )

        # Ensure <driver> exists
        driver = disk_element.find("driver")
        if driver is None:
            driver = ET.SubElement(disk_element, "driver")

        driver.set("name", "qemu")
        #driver.set("type", "qcow2")
        driver.set("cache", "none")
        driver.set("io", "native")
        driver.set("discard", "unmap")

        # Ensure <target> exists
        target = disk_element.find("target")
        if target is None:
            target = ET.SubElement(disk_element, "target")

        target.set("dev", f"nvme{disk_index}n1")
        target.set("bus", "nvme")

        # Remove drive-style address (SATA/SCSI)
        for address_element in list(disk_element.findall("address")):
            if address_element.get("type") == "drive":
                disk_element.remove(address_element)
            if address_element.get("type") == "pci":
                disk_element.remove(address_element)

        # Generate unique serial per disk
        digest = hashlib.sha256(
            f"{vm_uuid}-{disk_index}".encode("utf-8")
        ).hexdigest()
        serial_value = "S5G" + digest[0:17]  # 20 chars total

        serial = disk_element.find("serial")
        if serial is None:
            serial = ET.SubElement(disk_element, "serial")
        serial.text = serial_value


def looking_glass():
    # SPICE audio (top-level, idempotent)
    for audio in root.findall("audio"):
        if audio.get("type") == "spice":
            root.remove(audio)

    ET.SubElement(root, "audio", {
        "id": "1",
        "type": "spice"
    })

    # Looking Glass ivshmem (must be under <devices>)
    devices = root.find("devices")
    if devices is None:
        print("Error: no <devices> section found in XML")
        sys.exit(1)

    # Remove existing LG shmem
    for shmem in devices.findall("shmem"):
        if shmem.get("name") == "looking-glass":
            devices.remove(shmem)

    shmem = ET.SubElement(devices, "shmem", {
        "name": "looking-glass"
    })

    ET.SubElement(shmem, "model", {
        "type": "ivshmem-plain"
    })

    size = ET.SubElement(shmem, "size", {
        "unit": "M"
    })
    size.text = "128"

def other_performance_optimizations():
    #find features tag
    features = root.find("features")
    if features is None:
        print("Error: no <features> element found")
        sys.exit(1)

    # sets interrupts to be handled by kvm instead of by qemu
    ioapic=features.find("ioapic")
    if ioapic is None:
        ioapic = ET.SubElement(features, "ioapic")
    ioapic.set("driver","kvm")

def transparency_optimization():
    #CPU: disable hypervisor bit
    cpu = root.find("cpu")
    if cpu is None:
        print("Error: no <cpu> element found")
        sys.exit(1)

    #find features tag
    features = root.find("features")
    if features is None:
        print("Error: no <features> element found")
        sys.exit(1)

    # hide kvm
    kvm = features.find("kvm")
    if kvm is None:
        print("this is none")
        kvm = ET.SubElement(features, "kvm")

    hidden = kvm.find("hidden")
    if hidden is None:
        hidden = ET.SubElement(kvm, "hidden")

    hidden.set("state", "on")

    hyperv = features.find("hyperv")

    if hyperv is None:
        hyperv = ET.SubElement(features, "hyperv")

    vendor_id = hyperv.find("vendor_id")
    if vendor_id is None:
        vendor_id = ET.SubElement(hyperv, "vendor_id")

    # choose vendor string based on cpu_vendor arg
    if cpu_vendor.lower() == "amd":
        vendor_value = "AuthenticAMD"
    else:
        vendor_value = "GenuineIntel"

    vendor_id.set("state", "on")
    vendor_id.set("value", vendor_value)

    # use real computer smbios
    os = root.find("os")
    if os is None:
        print("Error: no <os> element found")
        sys.exit(1)
    
    smbios = os.find("smbios")
    if smbios is None:
        smbios = ET.SubElement(os,"smbios")
    smbios.set("mode","host")

def asus_laptop_stuff():
    # Add xmlns:qemu to <domain> if not present
    if "xmlns:qemu" not in root.attrib:
        root.set("xmlns:qemu", "http://libvirt.org/schemas/domain/qemu/1.0")

    # Find existing qemu:commandline
    ns = {"qemu": "http://libvirt.org/schemas/domain/qemu/1.0"}
    cmdline = root.find("qemu:commandline", ns)
    if cmdline is None:
        cmdline = ET.SubElement(root, "{http://libvirt.org/schemas/domain/qemu/1.0}commandline")

    # Remove previous args if they exist to be idempotent
    for arg in cmdline.findall("{http://libvirt.org/schemas/domain/qemu/1.0}arg"):
        cmdline.remove(arg)

    # Add the two required args
    ET.SubElement(cmdline, "{http://libvirt.org/schemas/domain/qemu/1.0}arg", {"value": "-acpitable"})
    ET.SubElement(cmdline, "{http://libvirt.org/schemas/domain/qemu/1.0}arg", {"value": "file=/var/lib/libvirt/images/fakebattery.aml"})    

huge_pages()
cpu_layout()
cpu_pinning()
nvme_emulation()
other_performance_optimizations()
#scsi()
if virtual_machine_preset == "WindowsDisguised":
    transparency_optimization()
if is_laptop == "y" or is_laptop == "1":
    asus_laptop_stuff()

looking_glass()

tree.write(xml_path)
