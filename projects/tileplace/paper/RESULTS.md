# TilePlace results snapshot

> **2026-09-29 provenance audit:** A full diffeq timing replay does not reproduce
> the archived V4 trajectory. With the same hashed timing report, the current
> port parser yields 52 initial edges instead of 37. Four development summaries
> plus pdc/dsip disagree with the current parser and match a diagnostic
> restricted-port variant. Archived QoR values remain intact, but the
> single-frozen-implementation / outcome-blind held-out claim is **not verified**.
> Numerical gate checks alone do not close this gap. See
> `../experiments/tileplace_v4_timing_parser_audit_2026-09-29.json`.


## Prospective source-sealed local cohort completed (2026-09-29)

All 13 cases finished under protocol `c548ad1e181551cdfb0bbbf5409a49f833bd994b177110675d5ca77574b8df72` and implementation `2fa6e2324a971d8489bba12d49115f91d0a56874c0ee5200224d72e4f8a9f689`. Nine completed paired evaluation with identical full trajectories across two repetitions; the independent final audit verified 404 native trials. Seven improved CPD and two preserved it. Successful-subset geometric means are CPD -1.944246% and wirelength -0.213172%. These are 9-case subset statistics, not a 13-case success claim.

All four failures remain in the full denominator: adder lacks the required architecture model; ex1010, s298 and s38417 have legal native baselines but CPU input generation retains 8, 2 and 2 overused resources after the fixed 30 iterations, respectively. Refinement was not launched for those cases. No retries or architecture/parameter changes occurred. Static timing uses completed CPU paths with proxy edge delays; native VPR supplies final QoR. The cohort does not establish strict historical blindness or architecture generalization. Full evidence and all-case table: `../experiments/tileplace_new_cohort_2026-09-29/RESULTS.md`, `summary.json`, and `final_audit.json`.

The manuscript now includes this cohort in its abstract, results, limitations and conclusion. After compressing repeated historical descriptions, the rebuild has nine pages (eight body pages plus references), with no final-log overfull boxes or undefined references/citations. All nine rendered pages were visually reviewed without overlap, clipping or out-of-column tables. The complete make flow regenerates the audited cohort table before compiling.

## Fixed-source frontier suppression ablation (2026-09-29)

All 16 runs completed under implementation fed524e17a50f352ec6b6e08e12301bbf2c7df46d4b7f5a1faff71068c0a95d9. Two repeats per arm/design matched full search behavior. The paired audit verified 272 native trials. Enabling rejected-singleton proposal suppression produced no CPD improvement over disabling it on any of four observed development designs. Wirelength geometric mean changed by -0.013735%; only diffeq improved (9103 to 9098), while its closure calls increased from 8 to 16. Frisc, elliptic and clma had identical final QoR and calls in both arms (16, 16 and 24 respectively). Elliptic termination differed (epoch limit versus stalled frontier), despite equal outcomes.

This isolates proposal suppression with unchanged rejection tracking and stopping rules. It does not establish that suppression causes the current development CPD improvement. Historical parser-mixed comparisons remain separately archived and cannot supersede this fixed-source ablation. Evidence: `../experiments/tileplace_frontier_ablation_audit_2026-09-29.json`. No parameters were retuned.

## Fixed-source development replay completed (2026-09-29)

The generic-indexed-port-v1 implementation `0f8a684ae7dc745fceb257d62a71bd8f34f61bf41db5cc515dfb641b6557d2a3` passed four observed-development cases. The independent artifact audit verified all 176 native VPR trials, candidate/report bindings and repeat equality (costs, decisions, feedback and layouts).

| Case | CPD change | Wirelength change | Exact repeats |
|---|---:|---:|---:|
| diffeq | 0.000% | -0.055% | 4 |
| frisc | -6.261% | +0.310% | 2 |
| elliptic | -0.765% | +0.329% | 2 |
| clma | -0.134% | +0.086% | 2 |
| Geometric mean | -1.825% | +0.168% | — |

Evidence: `../experiments/tileplace_fixed_development_2026-09-29/summary.json` and `../experiments/tileplace_fixed_development_audit_2026-09-29.json`. This establishes current fixed-source development reproducibility. These previously observed cases do not provide new blind validation or resolve historical parser drift. The finalizer successfully generated the audited table and a nine-page manuscript (eight body pages and one references page). No physical-U280 performance evidence was added.

## V4 archived routed-oracle evaluation (numerical gates pass; provenance unresolved)

V4 adds routed top-path/congestion feedback, native VPR acceptance, exact rollback,
stable batch bisection, and an incumbent-specific no-good frontier.  Its sealed
configuration is timing/routed-timing/congestion weight 2/2/1, 20 setup paths,
four epochs, and at most 24 closures.  The four-case development matrix has CPD/WL
geomean changes of -0.804%/+0.026%, with strict CPD improvement on 3/4 cases.

| Case | Baseline WL | V4 WL | Δ WL | Baseline CPD (ns) | V4 CPD (ns) | Δ CPD |
|---|---:|---:|---:|---:|---:|---:|
| pdc | 55522 | 55395 | -0.229% | 8.34180 | 8.34180 | 0.000% |
| dsip | 8014 | 8014 | 0.000% | 2.71781 | 2.71781 | 0.000% |
| bnn | 1241876 | 1241362 | -0.041% | 8.86574 | 8.71729 | -1.674% |
| gemm_layer | 925591 | 926923 | +0.144% | 5.35581 | 5.07134 | -5.311% |
| tdarknet_like.small | 4043804 | 4054716 | +0.270% | 20.3741 | 16.0366 | -21.289% |
| ucsb_152_tap_fir | 86522 | 83805 | -3.140% | 4.97284 | 4.97284 | 0.000% |
| Six-case geomean | — | — | **-0.507%** | — | — | **-5.049%** |

All five preregistered publication clauses pass: all six outputs are native legal;
CPD geomean ratio is 0.94951 ≤0.99; three cases strictly improve CPD; WL geomean
ratio is 0.99493 ≤1.0025; and the maximum per-case WL ratio is 1.002698 ≤1.005.
`tdarknet_like.small` used 20/24 closures and accepted eight transactions.  The
frozen matrix is `tileplace_v4_heldout_matrix_2026-09-05.json`, SHA-256
`744a02558869acc6baafbced927f3bf16fdd12690bcd08bce00d0accd22498cf`.

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
| Titan23 stereo_vision (post-freeze) | 592827 | 593627 | +0.135% | 7.51746 | 7.51592 | -0.020% | 15→14 |
| Ten-case geomean | — | — | **-0.066%** | — | — | **-0.911%** | — |

原四例开发集保持 WL/CPD geomean -0.152%/-0.022%。冻结后才运行的
spmv/softmax/attention_layer/Titan23 neuron/stereo_vision 验证集为 +0.015%/-1.797%；五例 CPD 均不回归。
attention_layer 同时改善 WL 0.331% 与 CPD 7.069%；第二架构族 Titan23 neuron 诚实保留
WL +0.088%、CPD 不变及 routing iterations 15→16 的结果。此前已用于 4×4 macro probe 的
conv_layer 不计入 post-freeze 验证集；最终 2×2/q60000 策略在其 43 macros/86 members
上得到 WL -0.124%、CPD 不变。十例最坏单例 WL/CPD 变化仍为 +0.439%/+0.017%，5/10
案例 WL 改善、9/10 CPD 不回归。共 280205 条 routed connections 全部映射到 source/sink
clustered blocks；其中 275654 条映射到 atom timing pin，4551 条被显式
标为 unmapped、criticality 置零但仍保留在线长目标中。全部 CPU 确定性复跑 placement
SHA-256 一致。十例矩阵为 `timing_titan_stereo_extended_matrix_2026-09-02.json`；此前九例
Titan、八例 macro 与七例严格 timing-export 基矩阵仍分别保留为
`timing_titan_extended_matrix_2026-09-01.json`、`timing_macro_extended_matrix_2026-08-31.json`
和 `timing_extended_matrix_2026-08-31.json`。

## Native fixed-I/O QoR (separate cohort)

VTR 官方 `apex4_io_constraint.xml` 案例在结果产生前单独预注册，并使用同一冻结
2×2/q60000 策略。2,263/2,263 条 routed connections 均映射 clustered endpoints 与 atom
timing pins；两次完整 CPU placement/report 逐字节一致，28 个 coordinate-fixed I/O 全部
保持。non-Eigen correctness VPR 重读同一 XML 后，结果为：

| Case | Baseline WL | TilePlace WL | Δ WL | Baseline CPD (ns) | TilePlace CPD (ns) | Δ CPD | Route iters |
|---|---:|---:|---:|---:|---:|---:|---:|
| apex4 fixed-I/O | 10023 | 10044 | +0.210% | 5.20192 | 5.22600 | +0.463% | 19→21 |

该轻微双指标回退被保留，证明的是冻结 refinement 可在原生 fixed-I/O 约束下确定性闭环，
不是约束案例 QoR 改善。证据为 `constrained_qor_matrix_2026-09-01.json`；它不计入主
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
数据，并输出由 Vivado 重放和路由的 placement Tcl。它们均不能保持当前十例 QoR
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

以下计时属于早期 guarded reference，不能作为 V4 routed-oracle 总耗时。V4 还需支付
接受及拒绝候选的原生 route/analysis 与反馈刷新成本；closure 次数上限不等于运行时间
上限。目前没有受控重复的 V4 端到端计时或等时间预算对比，不能据 QoR 推导效率收益。

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

## V4 archived oracle cost audit (2026-09-29)

下表来自冻结六例搜索报告引用的原生 closure JSON，逐份验证 SHA-256 后汇总 `wall_s`。
计时范围是同步 VPR 子进程，不含 proposal、反馈刷新、driver 校验/哈希、初始输入和 baseline。
这只是所选冻结轨迹的单次历史观测，不是受控重复计时、V4 端到端运行时间或全部历史实验成本。
中断和基础设施重试轨迹不在该汇总中。

| Case | Calls | Accepted closures | VPR subprocess sum (s) | Rejected-call sum (s) |
|---|---:|---:|---:|---:|
| pdc | 16 | 1 | 56.155 | 52.577 |
| dsip | 16 | 0 | 17.420 | 17.420 |
| bnn | 16 | 2 | 1572.893 | 1377.711 |
| gemm_layer | 15 | 3 | 1446.111 | 1153.095 |
| tdarknet_like.small | 20 | 8 | 48573.013 | 29114.843 |
| ucsb_152_tap_fir | 24 | 2 | 664.857 | 608.326 |

其中 tdarknet 的 VPR 子进程累计约 13.49 小时，拒绝候选约 8.09 小时。候选评分加速不会
自动消除这些路由调用；尚不能从局部实现加速推导端到端加速。Accepted closures 与
accepted transactions 不同：一次 closure 可接受多个事务。

证据：`tileplace_v4_oracle_cost_audit_2026-09-29.json`；生成器：
`../tools/prepare_v4_oracle_cost_audit.py`。此审计不改变原 QoR 矩阵及预注册验收条件。

## Claim boundary

这些结果支持“确定性、约束感知、逐 connection timing 的增量 placement refinement”及
同 router 下的小幅几何平均 QoR 改善。它们不支持 U280 加速、能效或绝对 runtime claim。
VPR conventional/AP 的同 netlist 基线已闭合，但完整论文结论仍需更多 benchmark。
DREAMPlaceFPGA/AMF-Placer 的 B1 审计证明直接并表会改变问题定义；在另建外部格式实验前，
论文必须继续清楚限定为 VPR post-placement refinement，不能主张优于独立 placer。

## Current generic-parser development timing (2026-09-29)

The explicit `generic-indexed-port-v1` implementation was validated on the
previously observed diffeq development case. One warmup and all three measured
runs have identical candidate-placement hashes, decisions, final placement and
numerical feedback-content hashes. This restores repeatability for this one
current implementation/case, not the historical four-case gate or six-case
held-out aggregate.

| Measurement | Value |
|---|---:|
| Measured process wall samples (s) | 88.741, 89.655, 87.656 |
| Median complete process wall (s) | 88.741 |
| Sample wall-time CV | 1.128% |
| Median proposal evaluation (s) | 66.768 |
| Median oracle driver (s) | 20.067 |
| Median feedback refresh (s) | 0.424 |
| Median proposal / process fraction | 75.791% |
| Median oracle driver / process fraction | 22.571% |

Stage medians and per-run fraction medians are computed separately. CPU 31 is
fixed; the host is shared and filesystem cache is naturally warm. Process time
includes interpreter startup, provenance hashing and report/timing output, but
excludes precomputed baseline/input generation. `oracle_driver` includes its
validation, hashing and serialization as well as VPR execution.

All four observations end at 16 closures and one accepted transaction, with
CPD unchanged at 6.59759 ns and WL 9103→9098 (-0.055%). The historical restricted
parser's 6.53077 ns / 9105 result is not reproduced or used as the timing target.
The candidate evaluator is the largest measured component on this small case;
this does not override the large-case archived oracle-cost observations.

The first comparison incorrectly included raw route hashes whose headers embed
run directories. The amendment retains the first completed measurement and
compares exact numerical feedback plus parser identity; no measured sample was
discarded. Combined evidence is
`tileplace_v4_generic_timing_summary_2026-09-29.json`, generated by
`../tools/prepare_v4_generic_timing_summary.py`. There is no paired competitor,
acceleration claim, or broad performance conclusion from this pilot.

## Exact pressure-prefix optimization (2026-09-29)

Sparse horizontal/vertical integer prefix sums replace repeated unit-edge
walks in the L-path pressure calculation. Each feedback replacement rebuilds
the prefix index and invalidates net costs. The independent walk regression
covers sparse occupancy, negative coordinates, both path orders, refreshes,
and weights exceeding 64 bits.

On the same fixed generic-parser diffeq case, all optimized warmup/measured
runs exactly preserve candidate placements, transaction costs, proposal phase
records, decisions, feedback contents and final placement. Each version has
one warmup and three retained measured observations on CPU 31.

| Scope | Baseline median (s) | Prefix median (s) | Ratio |
|---|---:|---:|---:|
| Complete refinement process | 88.741 | 69.044 | 1.285× |
| Proposal evaluation | 66.768 | 47.724 | 1.399× |

Optimized process samples are 69.243, 68.674 and 69.044 s; sample CV is 0.419%.
Final CPD/WL remain 6.59759 ns/9098 with 16 closures and one accepted
transaction. Both versions use the current generic parser; neither restores
the historical restricted-parser development outcome.

The measurements are sequential on a shared host with naturally warm cache,
not randomized/interleaved; the process boundary excludes precomputed input
and baseline generation. This is one-case CPU prototype evidence, with no
FPGA performance or broad benchmark claim. Paired evidence is
`tileplace_v4_prefix_timing_comparison_2026-09-29.json`; its generator verifies
full trace/cost/feedback equivalence before emitting timing ratios. Both source
versions are retained under `experiments/implementation_sources/`, and the
baseline timing summary still reproduces byte-for-byte after the worktree edit.

## Static timing input interpretation (2026-09-29)

All four current source-sealed development reports bind static timing CSVs from PersistRoute balanced_pathreads iteration 0. external_timing.cpp sums quantized routed-path edge delays and supplies them to patched VPR/Tatum. Those static criticalities are proxy-derived; they are separate from native setup-path feedback and native routed CPD/WL used for acceptance. This source clarification does not change archived numerical QoR. New validation must freeze the delay-generation chain explicitly.
