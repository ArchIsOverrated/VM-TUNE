#!/usr/bin/env python3
import sys
import xml.etree.ElementTree as ET

if len(sys.argv) != 3:
    print("Usage: configure_xml.py <xml-path> <cpu-list>")
    sys.exit(1)

xml_path = sys.argv[1]
cpu_list_str = sys.argv[2]

print(f"Configuring XML at {xml_path} with CPU list: {cpu_list_str}")

cpus = [c.strip() for c in cpu_list_str.split(",") if c.strip()]

print(f"Parsed CPU list: {cpus}")

tree = ET.parse(xml_path)
root = tree.getroot()

# -----------------------------
# Add <memoryBacking><hugepages/>
# -----------------------------
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
cputune = root.find("cputune")
if cputune is None:
    cputune = ET.SubElement(root, "cputune")

print("Configuring cputune")

# Remove previous pins
for pin in list(cputune.findall("vcpupin")):
    cputune.remove(pin)

print("Removed existing vcpupin entries")

vcpu_elem = root.find("vcpu")
print("Looking for <vcpu> element:", vcpu_elem)
if vcpu_elem is None or not vcpu_elem.text:
    print("Error: no <vcpu> element found")
    sys.exit(1)


num_vcpus = int(vcpu_elem.text)

print(f"Number of vCPUs: {num_vcpus}")

# Only pin what the user gave
for v in range(min(num_vcpus, len(cpus))):
    ET.SubElement(cputune, "vcpupin",
                  {"vcpu": str(v), "cpuset": cpus[v]})

print("Added new vcpupin entries")
tree.write(xml_path)
print(f"Updated XML written to {xml_path}")