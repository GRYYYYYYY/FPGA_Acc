#!/usr/bin/env bash
set -euo pipefail
commit_root=$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)
commit_xrt_root=${NET_COMMIT_XRT_ROOT:-/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt}
commit_output=${1:?output executable required}
commit_mode=${2:-directed}
case "$commit_mode" in
 directed) commit_source=tb/net_commit_hbm_tb.cpp;;
 adversarial) commit_source=tb/net_commit_adversarial_tb.cpp;;
 *) exit 2;;
esac
mkdir -p "$(dirname "$commit_output")"
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -I"$commit_root/include" -I"$commit_root/tb" -isystem "$commit_xrt_root/include" \
 "$commit_root/host/net_commit_xrt.cpp" "$commit_root/$commit_source" "$commit_root/tb/net_commit_trace.cpp" \
 -Wl,--wrap=dieroute_net_commit_hbm -L"$commit_xrt_root/lib" -Wl,-rpath,"$commit_xrt_root/lib" -lxrt_coreutil -luuid -pthread -o "$commit_output"
