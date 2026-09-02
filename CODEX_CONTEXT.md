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

`projects/tileplace` 的 HLS kernel 仍是固定 512 instances/64 pages 的 toy 原型；但
独立 correctness 路径已新增真实 VPR JSONL contract、输入/输出 SHA-256 manifest、
不限规模 CPU golden、异构/subtile 唯一占用、region/fixed/macro/cascade validator
和 VPR `.place` 写回。五案例矩阵共 2866 clustered blocks/47580 connections，全部
CPU golden 与 VPR 原生 route+analysis 合法，iterations/WL/CPD 与冻结 baseline 一致。
Koios `conv_layer` 覆盖 42 DSP、56 memory、156 IO；同一精确 VTR commit
`8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07` 从 architecture direct/packed netlist 导出
43 个 carry macro/86 members，capture/contract/closure 哈希一致。非法异构 placement
经 CPU 确定性恢复后也通过 VPR 原生 consistency 与布通。VTR 官方 `bigkey_tight`
region 与 `apex4` fixed-I/O 两例又覆盖 686 blocks、176 constrained clusters/28
coordinate-fixed clusters；违规注入恢复均通过 VPR 原生重读 XML 后的 route+analysis，
证据为 `tileplace/experiments/external_constraints_matrix_2026-08-31.json`。这份约束矩阵
仍使用原 non-Eigen VPR binary，不能改写成 AP 约束结果。
另在结果产生前预注册 apex4 fixed-I/O constrained QoR 点，并以冻结 2×2/q60000 策略运行：
2263/2263 条 connection 完整映射、28 个 coordinate-fixed I/O 保持、两遍 CPU 逐字节一致；
原生 WL/CPD 为 +0.210%/+0.463%，19→21 iterations。该负结果单列于
`tileplace/experiments/constrained_qor_matrix_2026-09-01.json`，不进入九例主 aggregate，
也不是 Eigen AP 结果。

CPU 研究原型已加入 page/四着色、精确 touched-net 增量 cost、逐 connection
endpoint timing、q60000 critical-distance guard 和 macro-aware site/net 冲突事务。
九个 QoR contract 共 198595 条 routed connections 全映射 clustered endpoints；同 tile
多 IO sink 由 RR class stride 唯一映射 subtile，多高度 DSP/memory endpoint 按物理 tile
footprint 映射 placement root。2×2/4×4/8×8 消融在四例开发集上选择 2×2；冻结后依次加入
spmv/softmax/attention_layer 的七案例串行 VPR 矩阵 routed WL/CPD 几何平均为
-0.108%/-1.296%，最坏单例 +0.439%/+0.017%。冻结后三例自身为 -0.049%/-2.970%；
attention_layer 为 -0.331%/-7.069%，routing iterations 保持 15。证据为
`tileplace/experiments/timing_extended_matrix_2026-08-31.json`，其输入捕获审计为
`attention_layer_input_capture_2026-08-31.json`。另以最终 2×2/q60000 策略复验此前参与
4×4 probe 的 conv_layer：43 macros/86 members 保持，WL/CPD -0.124%/0.000%，14→15
routing iterations；它单列为 previously-probed macro-stress，不冒充 post-freeze。随后以同一
2×2/q60000 策略加入第二架构族 Titan23 neuron：101 macros/204 members 保持，WL/CPD
+0.088%/0.000%，15→16 routing iterations。九例 WL/CPD geomean 为 -0.088%/-1.010%，
最坏仍为 +0.439%/+0.017%；四个 post-freeze cases 为 -0.015%/-2.236%。证据为
`timing_titan_extended_matrix_2026-09-01.json`。198595 条 connection 中 194155 条映射
atom timing pin；conv_layer 其余 4440 条显式 zero-criticality/unmapped、仍保留在线长目标。
另以 Eigen 3.4.0 构建精确 revision 的独立 VPR binary
（SHA-256 `dd7d30f...`），在同 packed netlist/router 下配对 conventional SA 与官方
cluster-level AP + quench。六个 conventional 点精确复现冻结 baseline；AP 六例全合法，
但 WL/CPD geomean 为 +3.711%/+16.103%，0/6 WL 改善且 0/6 CPD 不回归。证据为
`tileplace/experiments/vpr_placement_baseline_matrix_2026-08-31.json`。这是实验性
wirelength-oriented 官方路径的可执行负结果，不代表外部 timing-driven placer。
DREAMPlaceFPGA `004494318...` 与 AMF-Placer `70d982881...` 已完成 license、源码、CLI、依赖和
格式的 B1 审计，证据为
`tileplace/experiments/external_placer_feasibility_2026-08-31.json`。前者改变 packing/netlist，
后者使用 Vivado primitive/Tcl backend，均不能直接加入九例 TilePlace QoR 矩阵；
当前仍无独立外部 placer B0 QoR、XRT/多 CU 或物理 U280 性能结果。

单核 Python runtime 已固定 CPU 31、3 warm-ups/7 measured runs：六案例中位数
0.545/1.513/1.581/4.052/59.672/21.798 s；新增 spmv/softmax CV 为 2.8%/2.2%。四例开发集
禁用 guard cost 的惰性跳过取得 1.439× geomean speedup，
全部 placement 哈希不变。fork-process proposal evaluation 在四案例 1/2/4/8 workers
下精确等价，但 clma 无受控 speedup，因此只证明并行语义，不能作为性能 claim。证据为
`tileplace/experiments/{cpu_runtime_matrix,runtime_guard_elision_ablation,parallel_proposal_matrix}_2026-08-31.json`。

## 当前下一步

1. [完成] 增加可审计的真实外部 fixed/region 约束案例。
2. [完成] page decomposition/page-size 消融、增量 net/per-connection timing cost、
   critical-distance guard 与 macro-aware 并行冲突已有九案例、两个架构族矩阵。
3. [完成] VPR conventional full placement 与 cluster-level AP 已用同 packed netlist/router
   形成六例矩阵；DREAMPlaceFPGA/AMF-Placer 已审计为不适合直接并表的 B1 candidates。
   优先扩展 post-freeze VPR/Koios 案例；外部 placer 若继续，应另建预注册的
   Bookshelf/FPGAIF/Vivado cohort。Python process scaling 已证明受支配，后续性能实现应转向
   C++/持久共享快照或 HLS。
   第二个 Titan23 `stereo_vision` 已 outcome-blind 预注册，但官方 1.06 GB Titan 输入镜像
   实测吞吐过低；只在取得与冻结 baseline 哈希一致的 BLIF/SDC 后继续。
4. 算法 correctness/QoR 冻结后，再进行 HBM layout、
   多 PE/XRT、HLS/RTL 和 U280 实现。
5. DREAMPlaceFPGA/AMF-Placer 只有在独立 cohort 内冻结输入、转换、packing、依赖、命令与
   统一后端，并归档本机 QoR 后才能从 B1 升为 B0。

新线程应直接采用 `SESSION_HANDOFF.md` 的“1.1 当前线程最终检查点”。不要重新实现
或重复运行已经冻结的五案例/macro/recovery closure，除非相关输入或代码发生变化；
外部约束、九案例 TilePlace timing 与六案例 VPR conventional/AP 矩阵现已冻结，下一步
优先整理论文叙事并只在预注册后扩展新案例；
不得为了补 baseline 强行构建已证明方法学不相容的外部 placer。

## 关键入口

- `SESSION_HANDOFF.md`：跨设备恢复、冻结结果和第一批 TilePlace 任务。
- `projects/实现状态.md`：真实验证与 claim 边界。
- `projects/真实数据与论文基线运行指南.md`：环境、数据和实验规则。
- `projects/persistroute/paper/README.md`：第一篇论文材料入口。
- `projects/tileplace/README.md`：第二篇工程现状和实现顺序。
