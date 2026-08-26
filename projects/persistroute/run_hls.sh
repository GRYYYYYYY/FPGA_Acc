#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
vitis_root="${PERSISTROUTE_VITIS_ROOT:-/tools/Xilinx/Vitis/2022.2}"
settings="$vitis_root/settings64.sh"
xrt_root="${PERSISTROUTE_XRT_ROOT:-/opt/xilinx/xrt}"
xrt_settings="$xrt_root/setup.sh"

if [[ ! -f "$settings" ]]; then
  echo "Vitis settings not found: $settings" >&2
  exit 2
fi
if [[ ! -f "$xrt_settings" ]]; then
  echo "XRT settings not found: $xrt_settings" >&2
  exit 2
fi
if [[ $# -gt 1 ]]; then
  echo "usage: $0 [search_legacy|search_hbm|scheduler|commit_legacy|commit_hbm]" >&2
  exit 2
fi

source "$settings"
source "$xrt_settings"
if [[ $# -eq 1 ]]; then
  export PERSISTROUTE_HLS_ONLY="$1"
fi
cd "$script_dir"
exec vitis_hls -f run_hls.tcl
