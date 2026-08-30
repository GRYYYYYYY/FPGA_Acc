# FPGA_Acc

面向 FPGA 布局布线的 FPGA 加速研究工作区，按 PersistRoute、TilePlace、RouteCast、DieRoute 和 FusionPAR 五个独立工程推进。

第一篇 PersistRoute 已完成当前无卡环境可完成的工程、QoR、RTL、U280 routed
implementation 与论文材料闭环；仍待有卡设备补端到端 runtime、功耗/能耗和重复
试验。当前开发重点已切换为第二篇 TilePlace 的真实 VPR placement 前端、CPU
golden、异构/macro 合法化和 VPR 写回验证。

主要入口：

- [`SESSION_HANDOFF.md`](SESSION_HANDOFF.md)：新 Codex 会话的完整交接存档与快速恢复清单；
- [`CODEX_CONTEXT.md`](CODEX_CONTEXT.md)：工作区总体状态和后续任务；
- [`projects/实现状态.md`](projects/实现状态.md)：已验证能力与研究边界；
- [`projects/真实数据与论文基线运行指南.md`](projects/真实数据与论文基线运行指南.md)：环境、真实数据和实验复现流程；
- [`projects/persistroute/README.md`](projects/persistroute/README.md)：PersistRoute 源码结构与构建方法；
- [`projects/persistroute/experiments/accelerated_pathfinder_hw_emu_2026-08-26.json`](projects/persistroute/experiments/accelerated_pathfinder_hw_emu_2026-08-26.json)：最新 U280 RTL 硬件仿真证据。
- [`projects/persistroute/experiments/u280_treeseed_hw_2026-08-29.json`](projects/persistroute/experiments/u280_treeseed_hw_2026-08-29.json)：最终 tree-seed 源码的 U280 routed implementation 证据；
- [`projects/tileplace/README.md`](projects/tileplace/README.md)：下一工程的真实前端与 correctness 实现顺序。

本仓库只跟踪源码、脚本、说明和紧凑实验清单。Vitis/Vivado 生成目录、XSim 运行现场、第三方下载仓库、论文 PDF、数据集和大型二进制产物由 `.gitignore` 排除；实验清单中的 SHA-256 用于核验本地归档。
