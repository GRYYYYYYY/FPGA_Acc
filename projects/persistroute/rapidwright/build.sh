#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
rapidwright_jar="${RAPIDWRIGHT_JAR:-/home/gry/.local/opt/rapidwright-2022.2.0/rapidwright-2022.2.0-standalone-lin64.jar}"
java_root="${RAPIDWRIGHT_JAVA_HOME:-/tools/Xilinx/Vivado/2022.2/tps/lnx64/jre11.0.11_9}"
source_file="$script_dir/src/main/java/edu/fpgaacc/persistroute/RapidWrightBridge.java"
classes="$script_dir/build/classes"

if [[ ! -f "$rapidwright_jar" ]]; then
  echo "RapidWright standalone jar not found: $rapidwright_jar" >&2
  echo "Set RAPIDWRIGHT_JAR to a RapidWright 2022.2-compatible jar." >&2
  exit 2
fi
if [[ ! -x "$java_root/bin/javac" ]]; then
  echo "javac not found: $java_root/bin/javac" >&2
  echo "Set RAPIDWRIGHT_JAVA_HOME to a JDK 11 installation." >&2
  exit 2
fi

mkdir -p "$classes"
"$java_root/bin/javac" -encoding UTF-8 -cp "$rapidwright_jar" -d "$classes" "$source_file"
echo "RapidWrightBridge build: PASS"

