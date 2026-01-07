trap 'echo "Error on line $LINENO while running: $BASH_COMMAND" | tee -a ./performancegoverner.log >&2' ERR

PERFORMANCE_MODE="$1"

if [ -z "$PERFORMANCE_MODE" ]; then
  echo "No performance mode"
  exit 1
fi

if [ "$PERFORMANCE_MODE" = "performance" ]; then
    cpupower frequency-set -g performance
elif [ "$PERFORMANCE_MODE" = "powersave" ]; then
    cpupower frequency-set -g powersave
fi
