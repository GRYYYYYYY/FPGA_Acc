#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
vivado_root="${PERSISTROUTE_VIVADO_ROOT:-/tools/Xilinx/Vivado/2022.2}"
settings="$vivado_root/settings64.sh"
xrt_root="${PERSISTROUTE_XRT_ROOT:-/opt/xilinx/xrt}"
xrt_settings="$xrt_root/setup.sh"

if [[ ! -f "$settings" ]]; then
  echo "Vivado settings not found: $settings" >&2
  exit 2
fi
if [[ ! -f "$xrt_settings" ]]; then
  echo "XRT settings not found: $xrt_settings" >&2
  exit 2
fi
source "$settings"
source "$xrt_settings"
cd "$script_dir"
exec vivado -mode batch -source run_vivado_ooc.tcl -notrace
