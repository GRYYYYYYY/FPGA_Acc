# FPGA_Acc

面向 FPGA 布局布线的 FPGA 加速研究工作区，按 PersistRoute、TilePlace、RouteCast、DieRoute 和 FusionPAR 五个独立工程推进。

各工程的当前状态和研究边界以各自 README、实验计划及最新交接文档为准。
运行环境与工具路径见 [`AGENTS.md`](AGENTS.md)；最近一次环境核验未发现可用的
物理 U280，编译、仿真和实现结果不能替代板卡性能证据。

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

2026-11-09 上传范围、被排除数据和恢复限制见
[`GITHUB_UPLOAD.md`](GITHUB_UPLOAD.md)。
