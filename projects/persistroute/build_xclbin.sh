#!/usr/bin/env bash
set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
platform="${1:-${PERSISTROUTE_PLATFORM:-}}"
target="${2:-hw}"
vitis_root="${PERSISTROUTE_VITIS_ROOT:-/tools/Xilinx/Vitis/2022.2}"
xrt_root="${PERSISTROUTE_XRT_ROOT:-/opt/xilinx/xrt}"
# A production-kernel synthesis worker peaks near 5.75 GiB PSS on this host;
# keep the 16 GiB reference build serial and allow larger hosts to override it.
synth_jobs="${PERSISTROUTE_SYNTH_JOBS:-1}"
impl_jobs="${PERSISTROUTE_IMPL_JOBS:-1}"
# The four search CUs are timing-critical only on the platform DATA clock.
# Keep a conservative, reproducible default for the 16 GiB reference host;
# callers can explicitly request a higher clock after timing closure.
kernel_freq_mhz="${PERSISTROUTE_KERNEL_FREQ_MHZ:-180}"
output_name="${PERSISTROUTE_OUTPUT_NAME:-$target}"

if [[ -z "$platform" ]]; then
  echo "usage: $0 /path/to/xilinx_u280_*.xpfm [hw|hw_emu]" >&2
  echo "or set PERSISTROUTE_PLATFORM" >&2
  exit 2
fi
if [[ ! -f "$platform" ]]; then
  echo "platform not found: $platform" >&2
  exit 2
fi
if [[ "$target" != "hw" && "$target" != "hw_emu" ]]; then
  echo "target must be hw or hw_emu" >&2
  exit 2
fi
if [[ ! "$output_name" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*$ ]]; then
  echo "PERSISTROUTE_OUTPUT_NAME must contain only letters, digits, '.', '_', or '-'" >&2
  exit 2
fi
if [[ ! -f "$vitis_root/settings64.sh" ]]; then
  echo "Vitis settings not found: $vitis_root/settings64.sh" >&2
  exit 2
fi
if [[ ! -f "$xrt_root/setup.sh" ]]; then
  echo "XRT settings not found: $xrt_root/setup.sh" >&2
  exit 2
fi
if [[ ! "$synth_jobs" =~ ^[1-9][0-9]*$ || ! "$impl_jobs" =~ ^[1-9][0-9]*$ ]]; then
  echo "PERSISTROUTE_SYNTH_JOBS and PERSISTROUTE_IMPL_JOBS must be positive integers" >&2
  exit 2
fi
if [[ ! "$kernel_freq_mhz" =~ ^[1-9][0-9]*$ ]]; then
  echo "PERSISTROUTE_KERNEL_FREQ_MHZ must be a positive integer in MHz" >&2
  exit 2
fi

source "$vitis_root/settings64.sh"
source "$xrt_root/setup.sh"
cd "$script_dir"
if [[ "${PERSISTROUTE_SKIP_HLS:-0}" != "1" ]]; then
  ./run_hls.sh
fi

out_dir="$script_dir/build/xclbin/$output_name"
temp_dir="$out_dir/_x"
log_dir="$out_dir/logs"
report_dir="$out_dir/reports"
mkdir -p "$out_dir" "$temp_dir" "$log_dir" "$report_dir"
v++ -l -t "$target" --platform "$platform" --config connectivity.cfg \
  --temp_dir "$temp_dir" \
  --log_dir "$log_dir" \
  --report_dir "$report_dir" \
  --kernel_frequency "$kernel_freq_mhz" \
  --vivado.synth.jobs "$synth_jobs" \
  --vivado.impl.jobs "$impl_jobs" \
  "$script_dir/build/search_hbm_kernel.xo" \
  "$script_dir/build/commit_hbm_kernel.xo" \
  -o "$out_dir/persistroute.xclbin"
sha256sum "$out_dir/persistroute.xclbin"
