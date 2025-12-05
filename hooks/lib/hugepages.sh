#!/bin/bash

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./hugepages.log >&2' ERR

VM_NAME="$1"
ACTION="$2"

if [ -z "$VM_NAME" ]; then
  echo "No VM Name"
  exit 1
fi

if [ -z "$ACTION" ]; then
  echo "No Action"
  exit 1
fi

# Number of 2MiB hugepages to use (same for all VMs with this script)
HUGEPAGE_SIZE_KB=$(grep Hugepagesize /proc/meminfo | awk '{print $2}')

if [ -z "$HUGEPAGE_SIZE_KB" ]; then
  echo "Cannot determine hugepage size"
  exit 1
fi

LIBVIRT_XML_DIR="/etc/libvirt/qemu"
VM_XML="$LIBVIRT_XML_DIR/$VM_NAME.xml"

if [ ! -f "$VM_XML" ]; then
  echo "VM XML file $VM_XML not found"
  exit 1
fi

VM_MEM_KIB=$(grep "<memory" "$VM_XML" | head -n 1 | sed -E 's/.*>([0-9]+)<.*/\1/')
echo "Memory in KiB: $VM_MEM_KIB"


if [ -z "$VM_MEM_KIB" ]; then
  exit 0
fi

HUGEPAGES=$((VM_MEM_KIB / HUGEPAGE_SIZE_KB))

# If nothing set or invalid, do nothing
if [ "$HUGEPAGES" -le 0 ] 2>/dev/null; then
  exit 0
fi

HUGEPAGES_SYS_FILE="/proc/sys/vm/nr_hugepages"

if [ ! -w "$HUGEPAGES_SYS_FILE" ]; then
  echo "Cannot write to $HUGEPAGES_SYS_FILE (need root)" >&2
  exit 1
fi

CURRENT_HUGEPAGES=$(cat "$HUGEPAGES_SYS_FILE")
TARGET_HUGEPAGES=0
ALLOCATED_HUGEPAGES=$(cat "$HUGEPAGES_SYS_FILE")

if [ "$ACTION" = "allocate" ]; then
  TARGET_HUGEPAGES=$((CURRENT_HUGEPAGES+HUGEPAGES))
elif [ "$ACTION" = "release" ]; then
  TARGET_HUGEPAGES=$((CURRENT_HUGEPAGES-HUGEPAGES))
fi

attempts=0
while [ "$attempts" -lt 1000 ] && [ "$ALLOCATED_HUGEPAGES" -ne "$TARGET_HUGEPAGES" ]; do
  echo 1 > /proc/sys/vm/compact_memory
  echo "$TARGET_HUGEPAGES" > "$HUGEPAGES_SYS_FILE"
  ALLOCATED_HUGEPAGES=$(cat "$HUGEPAGES_SYS_FILE")
  attempts=$((attempts+1))
done

if [ "$ALLOCATED_HUGEPAGES" -ne "$TARGET_HUGEPAGES" ]; then
  echo "Failed to set hugepages to $TARGET_HUGEPAGES (current: $ALLOCATED_HUGEPAGES)"
  exit 1
fi

exit 0
