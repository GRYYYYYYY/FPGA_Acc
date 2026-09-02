# FPGA_Acc Environment

## Scope and Portability

The concrete paths and hardware status below describe the current execution
environment verified on 2026-08-31. On a different machine, verify the
OS/kernel, Vitis/Vivado/Vitis HLS, XRT, XPFM path, memory/swap, disk space, and
`xbutil examine` output before running experiments. Update this file with that
machine's facts. Do not make board-performance claims unless the target card is
actually enumerated and the run logs are archived.

Current host facts:

- OS: Ubuntu 22.04.4 LTS
- Kernel: Linux 5.15.0-119-generic
- CPU: 128 logical CPUs (2 x Intel Xeon Gold 6530)
- Memory: 1.5 TiB total, approximately 1.3 TiB available at verification time
- Swap: none
- Workspace filesystem: 10 TiB GPFS, approximately 9.3 TiB available

## Xilinx Toolchain

- OS: Ubuntu 22.04.4 LTS
- Running kernel: Linux 5.15.0-119-generic (XRT DKMS built; module loading is
  denied by the current controlled environment)
- Vivado: 2022.2
- Vitis: 2022.2
- Vitis HLS: 2022.2
- XRT: 2.14.354 (2022.2), installed from the local package archive
- CMake/CTest: 3.22.1 (Ubuntu package), installed and verified

Before running Xilinx/Vitis commands, load:

    source /inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/Vitis/2022.2/settings64.sh

Load XRT separately with:

    source /inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt/setup.sh

## Alveo U280 Platform

The U280 development platform and XRT userspace payloads are extracted locally
under the same persistent GPFS directory. The deployment archive is not
installed system-wide; the matching XRT package is also registered in the
current container for its dependencies and DKMS integration.

U280 platform file:

    /inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/dev_platform/opt/xilinx/platforms/xilinx_u280_gen3x16_xdma_1_202211_1/xilinx_u280_gen3x16_xdma_1_202211_1.xpfm

Use this platform for Vitis `v++` compile/link/emulation commands.

Recommended variable:

    U280_PLATFORM=/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/dev_platform/opt/xilinx/platforms/xilinx_u280_gen3x16_xdma_1_202211_1/xilinx_u280_gen3x16_xdma_1_202211_1.xpfm

`platforminfo` successfully parses this XPFM, its `hw.xsa`, `hw_emu.xsa`,
XCU280 part, 300/500/100 MHz platform clocks, and 32 HBM pseudo-channels.

## XRT

The canonical persistent XRT 2.14.354 userspace payload is located at:

    /inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt

This nested `opt/xilinx/xrt` suffix is intentional because the packaged
`setup.sh` validates its installation-directory suffix. The current container
also has the DEB registered under `/opt/xilinx/xrt`, but that path is on the
non-persistent overlay filesystem and must not be the documented default.
Sourcing the persistent setup reports branch 2022.2 and hash
`43926231f7183688add2dccfd391b36a1f000bea`. The source package archive has SHA-256
`00f62fbf3e3b4972df96eb0a73191765f9a004c9cf86df9dff70450b32ccdbe0`:

    /inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_202220.2.14.354_22.04-amd64-xrt.deb

The persistent payload is sufficient for userspace tools and `hw_emu` once its
`setup.sh` is sourced. OS dependencies, OpenCL ICD registration, udev rules,
and DKMS are system-level state and may need restoration when a new container
is created. The `xocl` and `xclmgmt` DKMS modules built successfully for the running kernel
and are installed in `/lib/modules/5.15.0-119-generic/updates/dkms/`. Their load
attempts fail with `Operation not permitted` in the current controlled
environment, which is not booted with systemd as PID 1. Userspace XRT and
`hw_emu` support are available, but physical-card execution requires an
environment that permits module loading. Do not switch this workflow to an
Ubuntu 6.8 kernel because XRT 2.14.354 is incompatible with that kernel.

## Hardware Availability

The current execution environment does not provide the `lspci` command. PCI
sysfs exposes 344 devices but no Xilinx vendor (`0x10ee`) device. With XRT
2.14.354 installed, `xbutil examine` reports `0 devices found` and unknown
XOCL/XCLMGMT versions because the modules cannot be loaded. Treat the physical
U280 as unavailable unless both PCI enumeration and `xbutil examine` later
prove otherwise.

Therefore:

- U280 platform compilation is available.
- `v++` compile/link against the U280 `.xpfm` is available.
- software/hardware emulation artifacts may be built where supported.
- Vivado implementation for XCU280 is available.
- actual execution on a physical U280 card is NOT available.
- XRT userspace is available for `hw_emu`; project-specific emulation artifacts
  and `emconfig.json` are still required for an execution.
- Do not interpret absent hardware as an XPFM or compiler installation failure.

Vivado recognizes the following XCU280 parts:

    xcu280-fsvh2892-2L-e
    xcu280-fsvh2892-2LV-e

## Model and Long-Running Job Delegation

- Keep the primary agent on `gpt-5.6-sol` with `high` reasoning for architecture,
  algorithm exploration, diagnosis, implementation decisions, and report analysis.
- When agent tools are available, delegate long-running Vitis HLS, Vivado
  synthesis/implementation, Vitis `v++` link, routing, or bitstream generation to
  the project custom agent `vivado_monitor`.
- The monitoring agent uses `gpt-5.6-terra` with `medium` reasoning. Delegate the
  exact command, working directory, expected outputs, and completion criteria;
  require it to wait for process completion and return exit status and evidence.
- The primary agent retains ownership of code edits, constraint changes,
  optimization choices, interpretation of results, and user-facing conclusions.
- Do not spawn the monitoring agent for quick environment checks, short report
  reads, or commands expected to finish within a few minutes.
