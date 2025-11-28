#!/bin/bash
set -Eeuo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "Please run this script with sudo:"
  echo "  sudo $0"
  exit 1
fi

trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" >&2' ERR

# -----------------------------
# Detect mouse evdev device
# -----------------------------
detect_mouse_evdev() {
  echo "Detecting mouse evdev device..."

  # Find candidate mouse devices (by-id is usually the nicest)
  mapfile -t MOUSE_CANDIDATES < <(ls -1 /dev/input/by-id/*-event-mouse 2>/dev/null || true)

  if (( ${#MOUSE_CANDIDATES[@]} == 0 )); then
    echo "ERROR: No mouse candidates found in /dev/input/by-id/*-event-mouse" >&2
    return 1
  fi

  echo "I will probe these mouse candidates:"
  for dev in "${MOUSE_CANDIDATES[@]}"; do
    echo "  - $dev"
  done
  echo
  echo "When prompted, move your MAIN mouse like crazy for ~2 seconds."

  for dev in "${MOUSE_CANDIDATES[@]}"; do
    local evnode
    evnode=$(realpath "$dev")

    echo
    echo "Testing mouse device: $dev"
    read -r -p "Press Enter, then move the mouse now... " _

    # If we see any input event within 2 seconds, this is our mouse
    if timeout 2s dd if="$evnode" of=/dev/null bs=16 count=1 status=none 2>/dev/null; then
      echo "Detected mouse activity on: $dev"
      MOUSE_DEV="$dev"
      export MOUSE_DEV
      return 0
    else
      echo "No activity detected on: $dev"
    fi
  done

  echo "ERROR: Could not detect mouse device automatically." >&2
  return 1
}

# -----------------------------
# Detect keyboard evdev device
# -----------------------------
detect_keyboard_evdev() {
  echo "Detecting keyboard evdev device..."

  # Keyboard candidates (by-path usually gives the main PS/2 or primary keyboard)
  mapfile -t KBD_CANDIDATES < <(ls -1 /dev/input/by-path/*-event-kbd 2>/dev/null || true)

  if (( ${#KBD_CANDIDATES[@]} == 0 )); then
    echo "ERROR: No keyboard candidates found in /dev/input/by-path/*-event-kbd" >&2
    return 1
  fi

  echo "I will probe these keyboard candidates:"
  for dev in "${KBD_CANDIDATES[@]}"; do
    echo "  - $dev"
  done
  echo
  echo "When prompted, mash keys on your MAIN keyboard for ~2 seconds."

  for dev in "${KBD_CANDIDATES[@]}"; do
    local evnode
    evnode=$(realpath "$dev")

    echo
    echo "Testing keyboard device: $dev"
    read -r -p "Press Enter, then mash keys now... " _

    if timeout 2s dd if="$evnode" of=/dev/null bs=16 count=1 status=none 2>/dev/null; then
      echo "Detected keyboard activity on: $dev"
      KBD_DEV="$dev"
      export KBD_DEV
      return 0
    else
      echo "No activity detected on: $dev"
    fi
  done

  echo "ERROR: Could not detect keyboard device automatically." >&2
  return 1
}

# -----------------------------
# Generate evdev XML snippet
# -----------------------------
generate_evdev_xml() {
  local vm_name="$1"
  local xml_file="${2:-evdev-${vm_name}.xml}"

  if [[ -z "${vm_name:-}" ]]; then
    echo "ERROR: generate_evdev_xml needs a VM name as argument" >&2
    return 1
  fi

  if [[ -z "${MOUSE_DEV:-}" || -z "${KBD_DEV:-}" ]]; then
    echo "ERROR: MOUSE_DEV or KBD_DEV not set before generate_evdev_xml" >&2
    echo "       Did you run detect_mouse_evdev and detect_keyboard_evdev?" >&2
    return 1
  fi

  cat > "$xml_file" <<EOF
<input type='evdev'>
  <source dev='${MOUSE_DEV}'/>
</input>
<input type='evdev'>
  <source dev='${KBD_DEV}' grab='all' grabToggle='ctrl-ctrl' repeat='on'/>
</input>
EOF

  echo "Wrote evdev XML for VM '${vm_name}' to: $xml_file"
}

# -----------------------------
# Attach evdev XML to VM (libvirt official way)
# -----------------------------
attach_evdev_to_vm() {
  local vm_name="$1"
  local xml_file="$2"

  if [[ -z "${vm_name:-}" || -z "${xml_file:-}" ]]; then
    echo "ERROR: attach_evdev_to_vm needs VM name and XML file path" >&2
    return 1
  fi

  # Check that VM exists
  local state
  state=$(virsh domstate "$vm_name" 2>/dev/null | tr -d '\r' || true)
  if [[ -z "$state" ]]; then
    echo "ERROR: VM '${vm_name}' not found by virsh." >&2
    return 1
  fi

  echo "VM '${vm_name}' current state: $state"

  if [[ "$state" == "running" || "$state" == "paused" ]]; then
    echo "Attaching evdev devices to VM '${vm_name}' (persistent + live)..."
    virsh attach-device "$vm_name" "$xml_file" --config --live
  else
    echo "Attaching evdev devices to VM '${vm_name}' (persistent only, VM is not running)..."
    virsh attach-device "$vm_name" "$xml_file" --config
  fi

  echo "evdev devices attached via libvirt for VM '${vm_name}'."
}

# -----------------------------
# Example usage / main flow
# -----------------------------
# You probably already have VM_NAME from earlier in your script.
# For demo purposes, you can set it here or wire this block into your existing flow.

#VM_NAME="my-gaming-vm"

detect_mouse_evdev
detect_keyboard_evdev
#generate_evdev_xml "$VM_NAME" "evdev-${VM_NAME}.xml"
#attach_evdev_to_vm "$VM_NAME" "evdev-${VM_NAME}.xml"
