#!/usr/bin/env bash
set -euo pipefail
native_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
native_xrt_root=${SUMMARY_XRT_ROOT:-/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt}
native_output=${1:?output executable required}
mkdir -p "$(dirname "$native_output")"
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -I"$native_root/include" -isystem "$native_xrt_root/include" \
    "$native_root/host/owner_publish_native_xrt.cpp" "$native_root/host/net_commit_native_xrt.cpp" "$native_root/tools/route_native_parallel.cpp" \
    -L"$native_xrt_root/lib" -Wl,-rpath,"$native_xrt_root/lib" -lxrt_coreutil -luuid -pthread -o "$native_output"
