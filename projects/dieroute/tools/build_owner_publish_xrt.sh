#!/usr/bin/env bash
set -euo pipefail
publisher_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
publisher_xrt_root=${SUMMARY_XRT_ROOT:-/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt}
publisher_output=${1:?output executable required}
publisher_mode=${2:-test}
publisher_extra=()
case "$publisher_mode" in
    test) publisher_source=tb/owner_publish_hbm_tb.cpp;;
    replay) publisher_source=tools/replay_owner_publish_hbm.cpp;;
    native) publisher_source=tools/route_native_parallel.cpp; publisher_extra=("$publisher_root/host/net_commit_xrt.cpp");;
    *) exit 2;;
esac
mkdir -p "$(dirname "$publisher_output")"
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -I"$publisher_root/include" -isystem "$publisher_xrt_root/include" \
    "$publisher_root/host/owner_publish_xrt.cpp" "$publisher_root/$publisher_source" "${publisher_extra[@]}" \
    -L"$publisher_xrt_root/lib" -Wl,-rpath,"$publisher_xrt_root/lib" -lxrt_coreutil -luuid -pthread -o "$publisher_output"
