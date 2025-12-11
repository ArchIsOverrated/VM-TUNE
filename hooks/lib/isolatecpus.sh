#!/bin/bash

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./isolatecpus.log >&2' ERR

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

VM_XML="/etc/libvirt/qemu/$VM_NAME.xml"

# Gather all cpuset values from XML: "0-3,8,10-11"
VM_CPU_PINSET=$(grep "<vcpupin" "$VM_XML" \
  | sed -n "s/.*cpuset='\([^']*\)'.*/\1/p" \
  | paste -sd ',' -)

if [ -z "$VM_CPU_PINSET" ]; then
  echo "No CPU pinning found. Skipping isolation."
  exit 0
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

# --- IRQ AFFINITY HELPER ------------------------------------------------------

# Set all IRQs that support smp_affinity_list to the given CPU list.
# Keep it stupid simple: we don't try to be smart per-device, we just
# push everything to the chosen cores.
set_all_irq_affinity() {
  local cpulist="$1"

  for path in /proc/irq/[0-9]*; do
    local irq="${path##*/}"
    local file="$path/smp_affinity_list"

    if [ -w "$file" ]; then
      # Ignore errors on weird IRQs that refuse changes
      echo "$cpulist" > "$file" 2>/dev/null || true
    fi
  done
}

# --- ACTION LOGIC -------------------------------------------------------------

if [ "$ACTION" = "isolate" ]; then
  echo "Isolating VM cores. Host-only CPUs: $HOST_CPUS"
  systemctl set-property --runtime -- system.slice AllowedCPUs="$HOST_CPUS"
  systemctl set-property --runtime -- user.slice   AllowedCPUs="$HOST_CPUS"
  systemctl set-property --runtime -- init.slice   AllowedCPUs="$HOST_CPUS"

  echo "Setting IRQ affinity to host CPUs: $HOST_CPUS"
  set_all_irq_affinity "$HOST_CPUS"

elif [ "$ACTION" = "deisolate" ]; then
  echo "Restoring full CPU set: $ALL_CORES"
  systemctl set-property --runtime -- system.slice AllowedCPUs="$ALL_CORES"
  systemctl set-property --runtime -- user.slice   AllowedCPUs="$ALL_CORES"
  systemctl set-property --runtime -- init.slice   AllowedCPUs="$ALL_CORES"

  echo "Restoring IRQ affinity to all CPUs: $ALL_CORES"
  set_all_irq_affinity "$ALL_CORES"

else
  echo "Unknown action: $ACTION"
  exit 1
fi

