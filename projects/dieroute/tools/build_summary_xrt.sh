#!/usr/bin/env bash
set -euo pipefail
summary_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
summary_xrt_root=${SUMMARY_XRT_ROOT:-/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt}
summary_output=${1:?output executable required}
mkdir -p "$(dirname "$summary_output")"
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -I"$summary_root/include" -isystem "$summary_xrt_root/include" \
    "$summary_root/host/summary_hbm_xrt.cpp" "$summary_root/tb/summary_hbm_tb.cpp" \
    -L"$summary_xrt_root/lib" -Wl,-rpath,"$summary_xrt_root/lib" -lxrt_coreutil -luuid -pthread -o "$summary_output"
