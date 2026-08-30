# FPGA_Acc Environment

## Scope and Portability

The concrete paths and hardware status below describe the original verified
Ubuntu VMware environment as of 2026-08-31. On a different machine, verify the
OS/kernel, Vitis/Vivado/Vitis HLS, XRT, XPFM path, memory/swap, disk space, and
`xbutil examine` output before running experiments. Update this file with that
machine's facts instead of assuming `/tools`, `/opt/xilinx`, kernel 5.15, or the
absence of a physical U280. Do not make board-performance claims unless the
target card is actually enumerated and the run logs are archived.

## Xilinx Toolchain

- OS: Ubuntu 22.04.5 LTS
- XRT-compatible kernel: Linux 5.15.0-190-generic
- Vivado: 2022.2
- Vitis: 2022.2
- Vitis HLS: 2022.2
- XRT: 2.14.354 (2022.2)

Before running Xilinx/Vitis commands, load:

    source /tools/Xilinx/Vitis/2022.2/settings64.sh
    source /opt/xilinx/xrt/setup.sh

## Alveo U280 Platform

The U280 development and deployment platform packages are installed.

U280 platform file:

    /opt/xilinx/platforms/xilinx_u280_gen3x16_xdma_1_202211_1/xilinx_u280_gen3x16_xdma_1_202211_1.xpfm

Use this platform for Vitis `v++` compile/link/emulation commands.

Recommended variable:

    U280_PLATFORM=/opt/xilinx/platforms/xilinx_u280_gen3x16_xdma_1_202211_1/xilinx_u280_gen3x16_xdma_1_202211_1.xpfm

## XRT

XRT setup:

    /opt/xilinx/xrt/setup.sh

xbutil:

    /opt/xilinx/xrt/bin/xbutil

Installed XRT version:

    2.14.354

The `xocl` and `xclmgmt` DKMS modules are installed for:

    5.15.0-190-generic

Do not switch this workflow to the Ubuntu 6.8 kernel because XRT 2.14.354 is incompatible with that kernel.

## Hardware Availability

This environment is running inside VMware.

There is currently no physical Alveo U280 PCIe device passed through to this VM.

Therefore:

- U280 platform compilation is available.
- `v++` compile/link against the U280 `.xpfm` is available.
- software/hardware emulation may be used where supported.
- Vivado implementation for XCU280 is available.
- actual execution on a physical U280 card is NOT available.
- `xbutil examine` is expected to report `0 devices found`.
- Do not interpret `0 devices found` as an XRT/platform installation failure.

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
