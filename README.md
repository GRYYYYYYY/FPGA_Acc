# FPGA_Acc

面向 FPGA 布局布线的 FPGA 加速研究工作区，按 PersistRoute、TilePlace、RouteCast、DieRoute 和 FusionPAR 五个独立工程推进。

当前重点是 PersistRoute：项目已完成真实 VPR/FPGAIF 数据转换、PathFinder 控制层、4 个 Search CU + 1 个 Commit CU 的 U280 HBM/XRT 实现、HLS/RTL 验证、U280 布局布线，以及真实 VPR RR graph 子集上的多 CU、多轮 `hw_emu` golden 对照。

主要入口：

- [`CODEX_CONTEXT.md`](CODEX_CONTEXT.md)：工作区总体状态和后续任务；
- [`projects/实现状态.md`](projects/实现状态.md)：已验证能力与研究边界；
- [`projects/真实数据与论文基线运行指南.md`](projects/真实数据与论文基线运行指南.md)：环境、真实数据和实验复现流程；
- [`projects/persistroute/README.md`](projects/persistroute/README.md)：PersistRoute 源码结构与构建方法；
- [`projects/persistroute/experiments/accelerated_pathfinder_hw_emu_2026-08-26.json`](projects/persistroute/experiments/accelerated_pathfinder_hw_emu_2026-08-26.json)：最新 U280 RTL 硬件仿真证据。

本仓库只跟踪源码、脚本、说明和紧凑实验清单。Vitis/Vivado 生成目录、XSim 运行现场、第三方下载仓库、论文 PDF、数据集和大型二进制产物由 `.gitignore` 排除；实验清单中的 SHA-256 用于核验本地归档。
