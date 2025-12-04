#!/bin/bash

VM_NAME="$1"
ACTION="$2"

if [ -z "$VM_NAME" ] || [ -z "$ACTION" ]; then
  echo "Usage: $0 <vm_name> <isolate|deisolate>"
  exit 1
fi

VM_XML="/etc/libvirt/qemu/$VM_NAME.xml"

# Gather all cpuset values from XML: "0-3,8,10-11"
VM_CPU_PINSET=$(grep "<vcpupin" "$VM_XML" \
  | sed -n "s/.*cpuset='\([^']*\)'.*/\1/p" \
  | paste -sd ',' -)

if [ -z "$VM_CPU_PINSET" ]; then
  echo "No CPU pinning found."
  exit 1
fi

# Total host cores → "0-(TOTAL-1)"
TOTAL=$(nproc --all)
ALL_CORES="0-$((TOTAL - 1))"

# Simplified expand_list:
# Turns "0-3,8" → "0 1 2 3 8"
expand_list() {
  local input="$1"
  local out=""
  IFS=',' read -ra items <<< "$input"

  for part in "${items[@]}"; do
    if [[ "$part" == *"-"* ]]; then
      start=${part%-*}
      end=${part#*-}
      for ((i=start; i<=end; i++)); do
        out="$out $i"
      done
    else
      out="$out $part"
    fi
  done

  echo "$out"
}

GUEST_CPUS=$(expand_list "$VM_CPU_PINSET")

# Build HOST_CPUS = all cores except guest cores
HOST_CPUS=""
for ((c=0; c<TOTAL; c++)); do
  in_guest=0
  for g in $GUEST_CPUS; do
    if [ "$c" -eq "$g" ]; then
      in_guest=1
      break
    fi
  done

  if [ "$in_guest" -eq 0 ]; then
    if [ -z "$HOST_CPUS" ]; then
      HOST_CPUS="$c"
    else
      HOST_CPUS="$HOST_CPUS,$c"
    fi
  fi
done

# --- ACTION LOGIC -------------------------------------------------------------

if [ "$ACTION" = "isolate" ]; then

  echo "Isolating VM cores. Host-only CPUs: $HOST_CPUS"
  systemctl set-property --runtime -- system.slice AllowedCPUs="$HOST_CPUS"
  systemctl set-property --runtime -- user.slice   AllowedCPUs="$HOST_CPUS"
  systemctl set-property --runtime -- init.slice   AllowedCPUs="$HOST_CPUS"

elif [ "$ACTION" = "deisolate" ]; then

  echo "Restoring full CPU set: $ALL_CORES"
  systemctl set-property --runtime -- system.slice AllowedCPUs="$ALL_CORES"
  systemctl set-property --runtime -- user.slice   AllowedCPUs="$ALL_CORES"
  systemctl set-property --runtime -- init.slice   AllowedCPUs="$ALL_CORES"

else

  echo "Unknown action: $ACTION"
  exit 1

fi
