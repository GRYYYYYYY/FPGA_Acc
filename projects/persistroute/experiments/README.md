# PersistRoute 紧凑实验索引

本目录只提交可审计的紧凑 JSON；大型输入、逐轮输出、Vitis/Vivado 工程、xclbin
和 XSim 现场由 `.gitignore` 排除。论文结论优先使用下列 canonical evidence，不能
把单案例筛选或失败探针替换成最终矩阵。

## Canonical evidence

- `balanced_pathreads_corrected_matrix_2026-08-29.json`：最终六案例 VPR-native QoR
  汇总，6/6 legal、3 Balanced、6 Throughput；
- `tree_timing_weight128_spmv_full_2026-08-29.json`：最终 `spmv` weight-128 全量运行；
- `tree_timing_weight_sweep_diffeq_2026-08-29.json`：Q8 timing weight 选择；
- `spmv_timing_rootcause_2026-08-29.json`：高 fanout route-tree timing 根因；
- `u280_treeseed_hw_2026-08-29.json`：最终源码的 U280 routed implementation；
- `accelerated_pathfinder_hw_emu_2026-08-26.json`：最终 RTL `hw_emu` golden；
- `paper/generated/paper_results.json`（位于上级 `paper/`）：十案例 CPU 强基线。

## Exploratory/negative evidence

文件名含 `adaptive`、`softmax`、`spmv_3round`、单一 `tree_timing_weight` 或早期
`balanced_issue8` 的 JSON 是算法筛选、失败探针或单案例消融。它们用于解释机制
选择和防止重复试验，不是最终总体结果。旧 `spmv` 的 +57.911% CPD 是被拒绝的
诊断点；最终结果以 canonical weight-128 文件为准。

所有 C-model 时间只可用于同机算法诊断；没有物理 U280 日志时不得据此计算或
宣称板级加速比、功率或能耗。
