# Workspace Context

更新日期：2026-08-31。

## 总目标与当前位置

建立五个独立的 FPGA 加速 FPGA 布局布线论文工程，按
PersistRoute → TilePlace → RouteCast → DieRoute → FusionPAR 推进。

第一篇 PersistRoute 已完成当前无卡机器能够完成的工程、QoR、RTL、U280 实现和
论文材料闭环。当前主任务切换为第二篇 TilePlace 的真实 VPR 前端与 CPU golden；
PersistRoute 只保留物理 U280 runtime/功耗/重复试验这一外部硬件待补项。

## 共同原则

- 五篇论文共享基础设施，但必须分别具有独立问题、算法、硬件机制和实验结论。
- FPGA routing/placement 以 VPR、RWRoute/RapidWright、Vivado 等 FPGA 工作为依据；
  ASIC 文献只借鉴数据流、存储、调度和冲突处理。
- 未获得可执行代码或未冻结 commit/CLI 的基线只能标为 B1/B2，不能伪称复现。
- 所有硬件 claim 必须区分 HLS estimate、RTL cosim、`hw_emu`、routed implementation
  和物理上板；C-model/仿真墙钟不能代替真卡性能。
- 新设备必须重新核验工具版本、XPFM、内核/XRT兼容性、内存/swap、磁盘和板卡，
  不继承原 VMware 的环境假设。

## PersistRoute 冻结结果

- 生产 `Task` ABI 为 32 bytes，携带稳定 `net_id`，支持多 sink route-tree trunk。
- 8-bank MultiQueue、HBM Search/Commit、4 Search CU + 1 Commit CU、四份 Resource
  replica、batch/XRT host、差分同步和确定性重放均已实现。
- VPR 9/Tatum timing oracle 每轮反馈逐 connection criticality/slack；route tree 可
  写回 VPR `.route` 并通过原生 legality/consistency/STA 检查。
- candidate-path read set、tail serialization 和 route-tree upstream timing seed
  已完成。`spmv` CPD 从旧策略的 +57.91% 修复到 0.00%。
- 修正后的六案例全部合法；3 Balanced、6 Throughput，几何平均 WL/CPD 增量为
  `+5.466%/+1.550%`。证据为
  `projects/persistroute/experiments/balanced_pathreads_corrected_matrix_2026-08-29.json`。
- 十案例 CPU serial/16-worker 强基线完全配对，whole-flow/route-stage 几何平均为
  `1.046x/1.356x`；这不是硬件加速比。
- 最终 tree-seed 源码提交 `10856a2` 已完成 U280 `v++ hw`：180 MHz，
  WNS/TNS `+0.016/0 ns`，WHS/THS `+0.005/0 ns`，xclbin SHA-256
  `323ddd9f3170b8dccc2e76b63661971671da691390ff70984b62ba338cf18c57`。
  紧凑证据为 `projects/persistroute/experiments/u280_treeseed_hw_2026-08-29.json`。
- 已完成最终 `hw_emu` 与真实 RR graph 子集逐轮 golden；不要重跑。
- ACM/DAC LaTeX 位于 `projects/persistroute/paper/dac/`，允许当前正文超页，后期删减。

PersistRoute 未完成且只能在有卡设备补齐：物理 U280 端到端 runtime、功耗/能耗、
至少五次 measured runs、统计波动和最终加速比。实验协议已写入论文正文。

## TilePlace 当前状态

`projects/tileplace` 目前只有独立 HLS 原型：CLB/BRAM/DSP page capacity、region、
criticality、cascade 字段、确定性 page/site assignment 和 toy testbench。固定上限为
512 instances/64 pages；没有真实 VPR 前端、完整网表代价、macro/cascade 合法化、
CPU大规模golden、VPR写回、XRT、多CU或论文结果。

## 当前下一步

1. 在新设备复核环境并运行 TilePlace toy testbench，不先启动长 HLS/Vivado 作业。
2. 定义 VTR 9 placement 数据契约，复用 PersistRoute 冻结案例的架构、网表、seed、
   placement 和 timing 资产，但不要耦合两个工程的源码。
3. 实现真实 placement packer/manifest 与不限 512-instance 的 CPU golden，覆盖异构
   site、唯一占用、region、fixed block、macro/cascade 和确定性。
4. 写回 VPR placement，以同一 VPR router 做 legality、routed WL、CPD 和可布通性
   fail-closed 验证；先闭环 `diffeq`。
5. correctness 冻结后，再进行 page decomposition、增量 net/timing cost、HBM layout、
   多 PE/XRT、HLS/RTL 和 U280 实现。
6. 强基线从 VPR 9 placement 开始；DREAMPlaceFPGA/AMF-Placer 只有在 commit、依赖、
   命令与统一后端 router 固定后才能升级为可执行论文基线。

## 关键入口

- `SESSION_HANDOFF.md`：跨设备恢复、冻结结果和第一批 TilePlace 任务。
- `projects/实现状态.md`：真实验证与 claim 边界。
- `projects/真实数据与论文基线运行指南.md`：环境、数据和实验规则。
- `projects/persistroute/paper/README.md`：第一篇论文材料入口。
- `projects/tileplace/README.md`：第二篇工程现状和实现顺序。
