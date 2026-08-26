#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rapidwright_jar="${RAPIDWRIGHT_JAR:-/home/gry/.local/opt/rapidwright-2022.2.0/rapidwright-2022.2.0-standalone-lin64.jar}"
java_root="${RAPIDWRIGHT_JAVA_HOME:-/tools/Xilinx/Vivado/2022.2/tps/lnx64/jre11.0.11_9}"
rapidwright_root="${RAPIDWRIGHT_PATH:-$(dirname "$rapidwright_jar")}"
main_class="$script_dir/build/classes/edu/fpgaacc/persistroute/RapidWrightBridge.class"

if [[ ! -f "$main_class" ]]; then
  "$script_dir/build.sh"
fi
if [[ ! -x "$java_root/bin/java" ]]; then
  echo "java not found: $java_root/bin/java" >&2
  exit 2
fi
if [[ ! -d "$rapidwright_root/data" ]]; then
  echo "RapidWright data directory not found: $rapidwright_root/data" >&2
  echo "Set RAPIDWRIGHT_PATH to the installation root containing data/." >&2
  exit 2
fi

export RAPIDWRIGHT_PATH="$rapidwright_root"
exec "$java_root/bin/java" -cp "$script_dir/build/classes:$rapidwright_jar" \
  edu.fpgaacc.persistroute.RapidWrightBridge "$@"
