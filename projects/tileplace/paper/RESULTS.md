# TilePlace results snapshot

## Frozen timing strategy

2×2 pages、四着色、source page 加八邻页候选；每个 proposal 精确重算 touched nets，
以 old/new site write-set 与 touched-net set 做冲突提交。Timing cost 是逐 connection 的
`criticality_q × source/sink Manhattan distance`。`criticality_q >= 60000` 的连接相对
输入 placement 不允许增距。VPR macro 作为不可拆分事务。

## Same-router VPR 9 results

| Case | Baseline WL | TilePlace WL | Δ WL | Baseline CPD (ns) | TilePlace CPD (ns) | Δ CPD | Route iters |
|---|---:|---:|---:|---:|---:|---:|---:|
| diffeq | 9103 | 9031 | -0.791% | 6.59759 | 6.59759 | 0.000% | 13→13 |
| frisc | 33182 | 33173 | -0.027% | 13.5879 | 13.5902 | +0.017% | 12→13 |
| elliptic | 27329 | 27449 | +0.439% | 8.79211 | 8.79211 | 0.000% | 12→13 |
| clma | 79857 | 79676 | -0.227% | 11.6084 | 11.5962 | -0.105% | 15→15 |
| conv_layer (macro stress; previously probed) | 232357 | 232069 | -0.124% | 5.12784 | 5.12784 | 0.000% | 14→15 |
| spmv (post-freeze) | 221106 | 221112 | +0.003% | 6.15322 | 6.15322 | 0.000% | 13→13 |
| softmax (post-freeze) | 127260 | 127491 | +0.182% | 9.19045 | 9.03444 | -1.698% | 18→17 |
| attention_layer (post-freeze) | 544069 | 542266 | -0.331% | 8.82262 | 8.19892 | -7.069% | 15→15 |
| Titan23 neuron (post-freeze) | 766630 | 767301 | +0.088% | 7.60292 | 7.60292 | 0.000% | 15→16 |
| Nine-case geomean | — | — | **-0.088%** | — | — | **-1.010%** | — |

原四例开发集保持 WL/CPD geomean -0.152%/-0.022%。冻结后才运行的
spmv/softmax/attention_layer/Titan23 neuron 验证集为 -0.015%/-2.236%；四例 CPD 均不回归。
attention_layer 同时改善 WL 0.331% 与 CPD 7.069%；第二架构族 Titan23 neuron 诚实保留
WL +0.088%、CPD 不变及 routing iterations 15→16 的结果。此前已用于 4×4 macro probe 的
conv_layer 不计入 post-freeze 验证集；最终 2×2/q60000 策略在其 43 macros/86 members
上得到 WL -0.124%、CPD 不变。九例最坏单例 WL/CPD 变化仍为 +0.439%/+0.017%，5/9
案例 WL 改善、8/9 CPD 不回归。共 198595 条 routed connections 全部映射到 source/sink
clustered blocks；其中 194155 条映射到 atom timing pin，conv_layer 剩余 4440 条被显式
标为 unmapped、criticality 置零但仍保留在线长目标中。全部 CPU 确定性复跑 placement
SHA-256 一致。九例矩阵为 `timing_titan_extended_matrix_2026-09-01.json`；此前八例 macro
矩阵与七例严格 timing-export 基矩阵仍分别保留为
`timing_macro_extended_matrix_2026-08-31.json` 和 `timing_extended_matrix_2026-08-31.json`。

## Native fixed-I/O QoR (separate cohort)

VTR 官方 `apex4_io_constraint.xml` 案例在结果产生前单独预注册，并使用同一冻结
2×2/q60000 策略。2,263/2,263 条 routed connections 均映射 clustered endpoints 与 atom
timing pins；两次完整 CPU placement/report 逐字节一致，28 个 coordinate-fixed I/O 全部
保持。non-Eigen correctness VPR 重读同一 XML 后，结果为：

| Case | Baseline WL | TilePlace WL | Δ WL | Baseline CPD (ns) | TilePlace CPD (ns) | Δ CPD | Route iters |
|---|---:|---:|---:|---:|---:|---:|---:|
| apex4 fixed-I/O | 10023 | 10044 | +0.210% | 5.20192 | 5.22600 | +0.463% | 19→21 |

该轻微双指标回退被保留，证明的是冻结 refinement 可在原生 fixed-I/O 约束下确定性闭环，
不是约束案例 QoR 改善。证据为 `constrained_qor_matrix_2026-09-01.json`；它不计入九例
unconstrained aggregate，也不计入六例 Eigen conventional/AP 表。

## Same-packed-netlist VPR placement baselines

另以同一 Eigen-enabled VPR binary、同一 packed netlist、seed、channel width、单 worker
router/analysis 配对运行常规 timing-driven simulated annealing（SA）与 VPR 官方
cluster-level `--enable_analytic_placer true`（AP + quench）。这里没有使用会重新 packing 的
integrated `--analytical_place`。

| Case | AP Δ WL vs. SA | AP Δ CPD vs. SA |
|---|---:|---:|
| diffeq | +0.901% | +9.335% |
| frisc | +1.751% | +5.934% |
| elliptic | +1.705% | +11.277% |
| clma | +1.146% | +15.008% |
| spmv | +11.728% | +57.474% |
| softmax | +5.452% | +4.936% |
| Six-case geomean | **+3.711%** | **+16.103%** |

六个 conventional 点均逐项复现冻结 baseline 的 WL、CPD 与 routing iterations；12 个点
均通过 contract legality、VPR placement/routing consistency 和 analysis。AP 的执行由
日志中的创建与 timer 双标记确认，六例均改变 placement，但 0/6 改善 routed WL、0/6
保持或改善 CPD。该 revision 的 legacy cluster-level AP 是实验性 wirelength-oriented
路径，源码仍将 timing-weight update 标为 TODO，因此这是可执行官方基线及负结果，不能
代表外部 timing-driven placer 的水平。证据为
`vpr_placement_baseline_matrix_2026-08-31.json`；单次 stage time 只作审计元数据。

## Independent placer feasibility

DREAMPlaceFPGA `004494318...`（BSD-3-Clause）与 AMF-Placer `70d982881...`
（Apache-2.0 basic implementation）的源码、CLI、依赖和格式已完成 B1 审计，见
`external_placer_feasibility_2026-08-31.json`。前者从 flat Bookshelf/FPGA Interchange
输入开始并自行 packing/legalization；后者读取 Vivado 提取的 primitive/device/timing
数据，并输出由 Vivado 重放和路由的 placement Tcl。它们均不能保持当前九例 QoR
packed-netlist、architecture 与 router，因此没有强行构建或写入现有 QoR 表。两者仍是
可执行源码候选，但不是已复现的 B0 基线；若运行，必须另建明确分离的
Bookshelf/FPGAIF/Vivado cohort。

## Ablations

- diffeq 的 `net max criticality × HPWL`：WL -0.428%，CPD +0.896%，拒绝。
- 逐 connection cost、无 guard：WL -0.143%，CPD +0.846%，拒绝。
- q60000 critical-distance guard：WL -0.791%，CPD 0.000%，选择。
- timing weight 1/2/4 在 q60000 下产生相同 placement。
- 2×2/4×4/8×8 page 的 WL geomean 为 -0.152%/-0.104%/-0.045%，CPD geomean
  均为 -0.022%；按预先声明的最小 WL geomean 规则选择 2×2。
- 再加逐事务 touched-net HPWL 不增的 wire0 guard：四案例 WL geomean +0.006%，受
  4×4 q60000 策略的 -0.104% 支配，拒绝为默认。

## Orthogonal correctness evidence

- Koios `conv_layer`：43 VPR macros/86 members 保持，确定性复跑一致，routed WL
  -0.158%，CPD 不变。
- VTR 官方 `bigkey_tight` region 与 `apex4` fixed-I/O：686 blocks、176 constrained
  clusters、28 coordinate-fixed clusters；违规注入、两次恢复和 VPR 原生闭环通过。
  apex4 另有上述单独预注册的 constrained QoR 负结果。

## CPU runtime and parallel semantics

固定 Intel Xeon Gold 6530 的 logical CPU 31，3 次 warm-up 后做 7 次 measured runs；计时
包含 contract load、优化、placement 写出、合法性验证和 JSON report。中位 wall time：

| Case | Median wall (s) | Wall CV |
|---|---:|---:|
| diffeq | 0.545 | 4.6% |
| frisc | 1.513 | 2.1% |
| elliptic | 1.581 | 15.0% |
| clma | 4.052 | 2.6% |
| spmv | 59.672 | 2.8% |
| softmax | 21.798 | 2.2% |

六案例中位数范围为 0.545--59.672 s；新增两例的原始样本和合并审计见
`cpu_runtime_validation_matrix_2026-08-31.json` 与 `cpu_runtime_sixcase_matrix_2026-08-31.json`。
跳过禁用 wire guards 的无效 before-cost 后，四例开发集 geomean implementation speedup 为
1.439×（1.338×--1.649×），placement 哈希不变。fork-process proposal evaluation 的
1/2/4/8-worker 输出在四案例精确一致，但 clma 中位数为
4.046/4.112/4.190/4.104 s，没有受控并行 speedup。因此论文只主张并行事务语义，不主张
Python prototype scaling。

## Claim boundary

这些结果支持“确定性、约束感知、逐 connection timing 的增量 placement refinement”及
同 router 下的小幅几何平均 QoR 改善。它们不支持 U280 加速、能效或绝对 runtime claim。
VPR conventional/AP 的同 netlist 基线已闭合，但完整论文结论仍需更多 benchmark。
DREAMPlaceFPGA/AMF-Placer 的 B1 审计证明直接并表会改变问题定义；在另建外部格式实验前，
论文必须继续清楚限定为 VPR post-placement refinement，不能主张优于独立 placer。
