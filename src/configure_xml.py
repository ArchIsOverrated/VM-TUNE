#!/usr/bin/env python3
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 3:
    print("Usage: configure_xml.py <xml-path> <cpu-list>")
    sys.exit(1)

xml_path = sys.argv[1]
cpu_list_str = sys.argv[2]
emulator_list = sys.argv[3]

cpus = [c.strip() for c in cpu_list_str.split(",") if c.strip()]

tree = ET.parse(xml_path)
root = tree.getroot()

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
# CPU pinning
# -----------------------------
def cpu_pinning():
    cputune = root.find("cputune")
    if cputune is None:
        cputune = ET.SubElement(root, "cputune")

    # Remove previous pins
    for pin in list(cputune.findall("vcpupin")):
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

huge_pages()
cpu_pinning()

tree.write(xml_path)
