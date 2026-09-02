# Codex 项目交接存档

更新日期：2026-09-01（Etc/UTC）。

## 1. 新设备/新会话首先执行

将仓库克隆到新设备的 Linux 原生文件系统，不要假定原机器的
`/home/gry/workspace/FPGA_Acc`、Xilinx 安装路径、内核、swap 或板卡状态仍然成立。

新会话必须先完整阅读：

1. `AGENTS.md`
2. `SESSION_HANDOFF.md`（本文件）
3. `CODEX_CONTEXT.md`
4. `projects/实现状态.md`
5. `projects/真实数据与论文基线运行指南.md`

推荐开场指令：

> 继续 TilePlace，目标是将现有结果整理到足以支撑第二篇论文成文。请先完整阅读 AGENTS.md、SESSION_HANDOFF.md、CODEX_CONTEXT.md、projects/实现状态.md 和 projects/真实数据与论文基线运行指南.md，并核对当前脏工作树；不要 clean/reset、删除第三方构建或覆盖未提交修改。九案例主 QoR、独立 apex4 fixed-I/O constrained QoR、六案例 conventional/AP 与 CPU runtime 已冻结，不要无故重跑。优先取得哈希匹配的 Titan 2.0.0 stereo_vision BLIF/SDC 后按预注册策略运行第二个 Titan23 点；若输入仍不可得，则继续整理论文正文与 claim/evidence，不得换版本或使用不匹配输入。PersistRoute 最终 hw_emu 不重跑；长时间 Vitis/Vivado 作业按 AGENTS.md 交给 vivado_monitor。

首次检查：

```bash
git status --short --branch
git log -3 --oneline --decorate
uname -a
free -h
swapon --show
df -h .
source <Vitis安装目录>/settings64.sh
source <XRT安装目录>/setup.sh
v++ --version
vivado -version | head
vitis_hls -version | head
xbutil --version
xbutil examine
find /opt/xilinx/platforms -name '*.xpfm' -print
```

如果新设备的版本或平台路径不同，先更新该设备工作区中的 `AGENTS.md`，再运行
任何 Xilinx 作业。只有 `xbutil examine` 真实发现目标卡后，才进入上板实验。

当前主机已于 2026-08-31 按上述清单复核，并于 2026-09-02 安装 XRT：Ubuntu 22.04.4、kernel
`5.15.0-119-generic`、128 CPUs、1.5 TiB RAM、无 swap、工作区约 9.3 TiB 可用；
Vitis/Vivado/Vitis HLS 2022.2、本地 U280 XPFM 与 XRT 2.14.354 用户态可用，`xbutil`
可执行。`xocl`/`xclmgmt` DKMS 已为当前内核构建，但受控环境拒绝加载模块；`lspci`
仍不存在，PCI sysfs 未枚举 U280，`xbutil examine` 报告 0 devices。故可进行
编译/仿真/实现与具备产物时的 `hw_emu`，但不允许真卡 claim。精确路径见 `AGENTS.md`。
XRT 用户态已从同一 DEB 额外解包到持久化 GPFS 路径
`/inspire/hdd/global_user/guoruiyuan-253208540291/U280_2022.2/xrt_runtime/opt/xilinx/xrt`；
后续会话默认 source 该目录的 `setup.sh`，不要依赖容器 overlay 中的 `/opt/xilinx/xrt`。

### 1.1 当前线程最终检查点

当前 Git HEAD 为 `5425cf5`，所有 TilePlace 新工具、测试、实验 JSONL 与文档修改仍在
未提交工作树中。工作树还含用户既有的 timing/packing report，禁止 `git clean`、
`git reset --hard` 或批量删除未跟踪文件。VTR 源码/构建和大型 work 目录位于已忽略的
`projects/tileplace/third_party/` 与 `projects/tileplace/work/`，缺少 Git 跟踪不代表
实验未完成。交接时没有 VPR、Vitis、Vivado、Vitis HLS 或 XSim 长作业在运行。
交接前 C++ testbench 通过，14 个 Python tests 全部通过，417 个 experiment JSON
均可解析；七/八/九案例及 constrained 矩阵重生成 SHA-256 不变，`git diff --check`
通过。九例矩阵 SHA-256 为
`0231c612fc0042789c1208b7ed5e22922acc8635b3e6e7b1141d7f00ff3aff2f`，constrained
矩阵 SHA-256 为
`49a39a6ef45fc09b42386ae3894fb3a0c00ef67bb40b5722ff27f0300797bea4`。

TilePlace 当前冻结证据：

- `projects/tileplace/experiments/correctness_matrix_2026-08-31.json`：五案例、2866
  blocks、47580 connections，CPU/VPR legality 全通过，原生指标与 baseline 一致；
- `projects/tileplace/experiments/koios_conv_layer_seed1_cw300/vpr_macro_capture.json`：
  VPR 从 architecture direct/packed netlist 导出 43 macros/86 members；
- `projects/tileplace/experiments/koios_conv_layer_seed1_cw300/real_legalization_probe.json`：
  三类非法 placement 的两次 CPU 恢复确定一致，`moved_from_input=15`；
- `projects/tileplace/experiments/koios_conv_layer_seed1_cw300/recovered_vpr_native_closure.json`：
  恢复结果通过 placement/routing consistency、14 轮布通和 analysis；
- 精确 VTR commit 为 `8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07`，VPR SHA-256 为
  `a90dc1b3380ebda705e85f176db0cc3d6be1b71ab9ee887db819febc8b62bafc`。
- `projects/tileplace/experiments/external_constraints_matrix_2026-08-31.json`：VTR 官方
  `bigkey_tight` region 与 `apex4` fixed-I/O 两例共 686 blocks、252 matched atoms、
  176 constrained clusters/28 coordinate-fixed clusters；真实违规注入、确定性恢复和
  VPR 原生重读 XML 后的 route+analysis 全通过。
- `projects/tileplace/experiments/constrained_qor_matrix_2026-09-01.json`：结果产生前单独
  预注册的 apex4 fixed-I/O QoR 点。冻结 2×2/q60000 策略接受 10 moves，2263/2263 条
  connection 映射 clustered endpoints 与 atom timing pins，278 条 guarded connection
  无增距，两次完整 CPU 输出逐字节一致，28 个 coordinate-fixed I/O 保持。non-Eigen
  correctness VPR 的 WL/CPD 为 10023→10044（+0.210%）/5.20192→5.22600 ns（+0.463%），
  iterations 19→21。该负结果不并入九例主 aggregate 或六例 Eigen AP 表。
- `projects/tileplace/experiments/page_incremental_probe_2026-08-31.json`：4×4 page、四着色、
  touched-net 增量 cost 与 macro-aware site/net 事务的三案例探针；Koios 原生 WL -0.158%/
  CPD 不变，bigkey +1 WL 点拒绝；diffeq 已由后续 timing guard 消融替代旧 tradeoff 点。
- `projects/tileplace/experiments/timing_guard_ablation_2026-08-31.json`：diffeq 的 net-max×HPWL、
  connection-star 和 q55000/q60000 guard 消融；q60000 将 routed WL 9103→9031 且 CPD
  保持 6.59759 ns，timing weight 1/2/4 placement 哈希一致。
- `projects/tileplace/experiments/timing_multicase_matrix_2026-08-31.json`：
  六案例共 58395 条 timed connections 全 endpoint 映射；多高度 DSP/memory endpoint
  按 tile footprint 映射 placement root。冻结 q60000 + 2×2 page 策略的 routed WL/CPD
  几何平均 -0.071%/-0.300%，最坏 +0.439%/+0.017%；全部 CPU 复跑哈希一致。
  spmv/softmax 是策略冻结后验证，自身 geomean +0.092%/-0.852%。wire0 消融仍只属于
  原四例开发集且受支配，不设为默认。
- `projects/tileplace/experiments/timing_extended_matrix_2026-08-31.json`：在不改变
  2×2/q60000/单 worker 冻结策略的前提下加入 Koios `attention_layer`。七例共
  100349/100349 条 timed connections 全映射，WL/CPD geomean -0.108%/-1.296%，最坏
  +0.439%/+0.017%，4/7 WL 改善、6/7 CPD 不回归。三个 post-freeze case 自身为
  -0.049%/-2.970%；attention_layer 为 -0.331%/-7.069%，15→15 routing iterations，
  372 accepted moves，CPU placement/report 独立复跑逐字节一致。
- `projects/tileplace/experiments/attention_layer_input_capture_2026-08-31.json`：归档
  attention_layer 冻结 architecture/circuit/net/place/route 哈希、6.7 GiB RR graph
  （6181188 nodes/91982111 edges）、41954 connections、完整逐连接 timing 与独立
  timing-export binary。26 条连接达到 q60000；timing CSV 的整数 CPD 为 8823 ps，
  原 VPR 日志为 8.82262 ns。QoR closure 仍只用冻结 correctness binary `a90dc1b...`。
- `projects/tileplace/experiments/timing_macro_extended_matrix_2026-08-31.json`：最终
  2×2/q60000 策略又复验此前参与 4×4 probe 的 conv_layer。该点明确标为
  `macro_stress_previously_probed`，不是 post-freeze。43 macros/86 members 保持，WL
  232357→232069（-0.124%）、CPD 5.12784 ns 不变、routing iterations 14→15。八例
  WL/CPD geomean -0.110%/-1.135%，5/8 WL 改善、7/8 CPD 不回归；三个 post-freeze
  case 的 -0.049%/-2.970% 结论不变。
- `projects/tileplace/experiments/timing_titan_extended_matrix_2026-09-01.json`：冻结策略未调参地
  加入第二架构族 Titan23 neuron 后的九例主矩阵。Titan 点保持 101 macros/204 members，
  13 accepted moves，WL 766630→767301（+0.088%）、CPD 7.60292 ns 不变、routing
  iterations 15→16；两次完整 CPU placement/report 逐字节一致。九例 WL/CPD geomean
  -0.088%/-1.010%，5/9 WL 改善、8/9 CPD 不回归；四个 post-freeze cases 为
  -0.015%/-2.236%。198595/198595 条 connection 映射 clustered endpoints，194155 条映射
  atom timing pin，唯一 4440 条 unmapped 仍来自 conv_layer。输入 provenance 见
  `titan23_neuron_input_capture_2026-09-01.json`。
- `projects/tileplace/experiments/titan23_stereo_vision_preregistration_2026-09-01.json`：第二个
  Titan23 点已在输入捕获与运行前冻结；本机缺 stereo BLIF/SDC，官方 1.06 GB Titan 2.0.0
  镜像实测数分钟仅传约 4 MiB，故尚未产生 QoR。4,268,032-byte 部分缓存位于 ignored
  `projects/tileplace/work/titan_download_2026-09-01/titan_release_2.0.0_blif.tar.gz`；它不是
  完整归档，不得解包后误用。冻结的 stereo BLIF/SDC SHA-256 分别为
  `515426efda12b7c0f9c2414871cdd6cb2d1c21619de151934201a26e1b815762` 和
  `392cbdc288bbabd7cbfa4edf638f6c644997ec5ca5cd06a451873b6b22c43e4c`。不得换版本或用
  不匹配输入替代。
- `projects/tileplace/experiments/conv_layer_input_capture_2026-08-31.json` 与
  `vpr_timing_export_optional_build_2026-08-31.json`：21,140 条 routed connections 全部
  保留且映射 clustered endpoints；16,700 条映射 atom timing pin，4,440 条显式标为
  unmapped/criticality 0 并仍进入 wire cost。独立 timing-export v2 SHA `58c84e68...`；
  correctness binary、strict timing v1 binary 与 source hash 均保持不变。
- `projects/tileplace/experiments/page_size_ablation_2026-08-31.json`：2×2/4×4/8×8
  的 WL geomean 分别 -0.152%/-0.104%/-0.045%，CPD geomean 均 -0.022%，选择 2×2。
- `projects/tileplace/experiments/cpu_runtime_matrix_2026-08-31.json`：固定 CPU 31、3 次
  warm-up/7 次 measured，四案例完整 Python flow 中位数 0.545/1.513/1.581/4.052 s；
  elliptic wall CV 15.0%，完整样本保留。
- `projects/tileplace/experiments/cpu_runtime_validation_matrix_2026-08-31.json` 与
  `cpu_runtime_sixcase_matrix_2026-08-31.json`：同协议新增 spmv/softmax 中位数
  59.672/21.798 s，CV 2.8%/2.2%；六例合并范围 0.545--59.672 s。
- `projects/tileplace/experiments/runtime_guard_elision_ablation_2026-08-31.json`：禁用
  wire guards 时跳过无效 before-cost，四案例 geomean speedup 1.439×、逐例
  1.338×--1.649×，placement 哈希不变。
- `projects/tileplace/experiments/parallel_proposal_matrix_2026-08-31.json`：四案例
  1/2/4/8 fork workers 的目标、冲突计数、逐 pass 与 placement 全精确一致；clma
  受控中位数 4.046/4.112/4.190/4.104 s，无 process scaling speedup，不作性能 claim。
- `projects/tileplace/experiments/vpr_placement_baseline_matrix_2026-08-31.json`：Eigen 3.4.0
  构建的同一精确 VTR revision（VPR SHA-256 `dd7d30f7...`）在六例同 packed netlist、seed、
  channel width 和单 worker router 下配对 conventional SA 与 cluster-level AP + quench。
  conventional 六例逐项复现冻结 WL/CPD/iterations；AP 六例均 legal，但 WL/CPD geomean
  为 +3.711%/+16.103%，最坏 +11.728%/+57.474%，0/6 WL 改善、0/6 CPD 不回归。
  integrated `--analytical_place` 未混入；单次 stage time 不作性能 claim。
- `projects/tileplace/experiments/external_placer_feasibility_2026-08-31.json`：固定
  DREAMPlaceFPGA `004494318...`（BSD-3-Clause）和 AMF-Placer `70d982881...`
  （Apache-2.0 basic）的源码、CLI、依赖及格式，均为 source-audited B1 candidates。
  DREAMPlaceFPGA 从 flat Bookshelf/FPGAIF 输入重新 packing/legalization；AMF-Placer 从
  Vivado implemented design 抽取 primitive/device/timing 并输出 Vivado Tcl。二者均不能
  保持当前九例 TilePlace QoR 的 VPR packed-netlist/architecture/router，未强行构建，
  也没有 B0 QoR claim。

实现入口与重要约束：

- `tools/capture_vpr_macros.py` 调同一 VPR revision 导出 `place_macros.echo`；受限为
  1 次 routing iteration 时 VPR 返回 2 是预期现象，但必须先出现 placement consistency
  成功和明确的 iteration-limit/unroutable 标记；
- `tools/tileplace_vpr.py pack` 现在必须提供 `--architecture` 和 `--native-macros`，并
  核对 packed-netlist architecture hash；validator/legalizer 将原生 macro 整体处理；
  endpoint mapper 必须按 RR block-type width/height 覆盖多 tile endpoint，不能退回仅比较
  placement root 坐标；
- 原生约束使用 `pack --vpr-constraints`，其与手写 `--constraints` JSON 互斥；importer
  保留 VPR atom regex/cluster 交集/region union/layer/subtile 和部分 fixed 维度；
- `tools/run_vpr_closure.py` 必须在隔离 work 中执行，因为 VPR 会改写 `.place` header
  并在 netlist 旁生成 `.net.post_routing`；runner 会再生 macro 并核对哈希；
- `tools/run_vpr_placement_baseline.py` 要求空 work、精确 VPR revision/SHA、同 contract
  netlist/seed/channel width，并以 AP 创建/timer 双标记确认 `--enable_analytic_placer`
  真正执行；suite 可 `--resume`，矩阵生成器会重哈希全部输出；
- 不要把零移动 CPU golden 或恢复 placement 的 WL/CPD 写成 TilePlace QoR 改进。

快速复核命令：

```bash
g++ -std=c++17 -O2 -Iprojects/tileplace/include \
  projects/tileplace/src/tileplace.cpp projects/tileplace/tb/tileplace_tb.cpp \
  -o /tmp/tileplace_tb && /tmp/tileplace_tb
python3 -m unittest discover -s projects/tileplace/tests -v
python3 projects/tileplace/tools/prepare_correctness_matrix.py \
  --output projects/tileplace/experiments/correctness_matrix_2026-08-31.json
python3 projects/tileplace/tools/prepare_timing_guard_ablation.py \
  --output projects/tileplace/experiments/timing_guard_ablation_2026-08-31.json
python3 projects/tileplace/tools/prepare_page_size_ablation.py \
  --output projects/tileplace/experiments/page_size_ablation_2026-08-31.json
python3 projects/tileplace/tools/prepare_timing_multicase_matrix.py \
  --output projects/tileplace/experiments/timing_multicase_matrix_2026-08-31.json
python3 projects/tileplace/tools/prepare_timing_extended_matrix.py \
  --output projects/tileplace/experiments/timing_extended_matrix_2026-08-31.json
python3 projects/tileplace/tools/prepare_timing_macro_extended_matrix.py \
  --output projects/tileplace/experiments/timing_macro_extended_matrix_2026-08-31.json
python3 projects/tileplace/tools/prepare_timing_titan_extended_matrix.py \
  --output projects/tileplace/experiments/timing_titan_extended_matrix_2026-09-01.json
python3 projects/tileplace/tools/prepare_constrained_qor_matrix.py \
  --output projects/tileplace/experiments/constrained_qor_matrix_2026-09-01.json
python3 projects/tileplace/tools/prepare_runtime_ablation.py \
  --before projects/tileplace/work/runtime_cpu31_eager_w3.json \
  --after projects/tileplace/experiments/cpu_runtime_matrix_2026-08-31.json \
  --output projects/tileplace/experiments/runtime_guard_elision_ablation_2026-08-31.json
python3 projects/tileplace/tools/prepare_parallel_proposal_matrix.py \
  --output projects/tileplace/experiments/parallel_proposal_matrix_2026-08-31.json
python3 projects/tileplace/tools/prepare_vpr_placement_baseline_matrix.py \
  --config projects/tileplace/experiments/vpr_placement_baseline_cases_2026-08-31.json \
  --reports projects/tileplace/experiments/vpr_placement_baselines_2026-08-31 \
  --build-provenance projects/tileplace/experiments/vpr_eigen_build_2026-08-31.json \
  --tileplace-matrix projects/tileplace/experiments/timing_multicase_matrix_2026-08-31.json \
  --output projects/tileplace/experiments/vpr_placement_baseline_matrix_2026-08-31.json
python3 -m py_compile projects/tileplace/tools/*.py
git diff --check
```

上述检查在交接前全部通过。当前主机已于 2026-09-02 安装系统 CMake/CTest 3.22.1；
TilePlace 临时目录 Release 配置、编译及 CTest 2/2 通过。外部 region/fixed、九案例
TilePlace timing 与六案例 VPR conventional/AP 矩阵
现已冻结，不应无故重跑对应 closure；下一步优先整理第二篇论文，并只在预注册后扩展新案例。外部 placer 已完成
B1 可行性审计，只有另建 Bookshelf/FPGAIF/Vivado cohort 才继续，不为凑 baseline 强行构建。
首次 Koios endpoint
部分映射产物保存在 `*_endpoints_partial_mapping`，只作修复审计，不得混入最终矩阵。
外部 fixed-I/O 矩阵仍来自 non-Eigen binary，不能把六例 unconstrained AP 结果改写成
AP 约束闭环。

## 2. 总体位置

总目标是依次完成五个独立论文工程：

```text
PersistRoute → TilePlace → RouteCast → DieRoute → FusionPAR
```

PersistRoute 是第一篇工程，当前已经完成本机可完成的工程闭环与论文草稿：真实
VPR/FPGAIF 数据转换、production ABI、PathFinder/MultiQueue、HBM Search/Commit、
4 Search CU + 1 Commit CU、XRT host、逐 connection timing feedback、原生 VPR
回写检查、HLS/RTL 验证、U280 routed implementation、真实 RR graph 子集多轮
`hw_emu`、CPU 强基线、QoR/消融材料和 ACM/DAC LaTeX 草稿。

PersistRoute 仍缺物理 U280 的端到端 runtime、功耗/能耗和重复试验。这些是外部
硬件待补项，不应阻塞第二篇 TilePlace。不得把 C-model 或 `hw_emu` 墙钟时间写成
真卡加速比。

当前工程明确为 `projects/tileplace`。HLS kernel 仍只是最多 512 instances、64 pages
的确定性 toy 骨架，但 CPU/VPR 研究路径已经完成真实 correctness 前端、外部 region/fixed
约束、原生 macro、page/incremental timing cost、九案例 routed QoR、独立 constrained
QoR、强基线和 runtime/消融闭环。论文与 claim matrix 已同步这些证据。当前不是从前端
重新开始，而是优先补预注册的第二个 Titan23 点（仅限哈希匹配输入）并将第二篇论文整理
成文；XRT host/U280 硬件化可作为后续方向，不能虚构真卡结果。

## 3. PersistRoute 最终冻结状态

源码与论文冻结提交链：

```text
8832cc0  Extend PersistRoute to heterogeneous timing cases
a11d429  Add route-tree-aware timing seeds
10856a2  Close spmv timing QoR with route-tree costs
```

最新正确性/QoR机制：

- timing oracle 使用 VPR 9 `AnalysisDelayCalculator`/Tatum，每轮反馈逐 connection
  setup criticality/slack，production `Task` ABI 保持 32 bytes；
- candidate-path read set 取代 explored-resource read set，避免大图出现大量伪冲突；
- tail serialization 在停滞后收窄 issue width，修复 `softmax` 的尾部合法化；
- route-tree upstream timing seed 对共享树节点加入 source-to-attachment 延迟代价，
  修复高 fanout `spmv` 的 CPD 失真；
- `spmv` 最终使用 Q8 weight 128，其余冻结案例使用 weight 0。

修正后的六案例原生 VPR 矩阵：

| Case | Rounds | WL delta | CPD delta | Tier |
|---|---:|---:|---:|---|
| diffeq | 22 | +4.427% | +0.579% | Balanced |
| frisc | 18 | +4.659% | +0.876% | Balanced |
| elliptic | 20 | +3.934% | +3.857% | Throughput |
| clma | 8 | +3.216% | +0.662% | Balanced |
| spmv | 21 | +7.770% | 0.000% | Throughput |
| softmax | 23 | +8.912% | +3.388% | Throughput |

六例全部 legal，3 例达到 Balanced（WL ≤ 5%、CPD ≤ 3%），全部 6 例达到
Throughput（WL ≤ 10%、CPD ≤ 5%）。几何平均 WL/CPD 增量为
`+5.466%/+1.550%`。核心证据：

```text
projects/persistroute/experiments/balanced_pathreads_corrected_matrix_2026-08-29.json
projects/persistroute/experiments/tree_timing_weight128_spmv_full_2026-08-29.json
projects/persistroute/experiments/tree_timing_weight_sweep_diffeq_2026-08-29.json
projects/persistroute/experiments/spmv_timing_rootcause_2026-08-29.json
```

CPU 强基线另有 4 VTR + 2 Titan23 + 4 Koios 共十案例；serial/16-worker 配对的
route/QoR 完全一致，whole-flow/route-stage 几何平均为 `1.046x/1.356x`。这只是
CPU baseline，不是 PersistRoute 硬件加速比。

## 4. PersistRoute 硬件证据

最终 tree-seed 源码在 U280 平台完成完整 `v++ hw`：

```text
source commit: 10856a2
target clock: 180 MHz
WNS/TNS: +0.016 ns / 0
WHS/THS: +0.005 ns / 0
setup/hold failing endpoints: 0 / 0
xclbin SHA-256: 323ddd9f3170b8dccc2e76b63661971671da691390ff70984b62ba338cf18c57
```

可提交证据：

```text
projects/persistroute/experiments/u280_treeseed_hw_2026-08-29.json
```

大型 xclbin/报告目录被 `.gitignore` 排除，不会随 GitHub 自动迁移。原机器保留：

```text
build/xclbin/hw/persistroute.xclbin
  e3ca2e6030aa5b65d07390492e8d7070fcf74cd29064318cc7139c3e3ea69743
build/xclbin/hw_pathreads_2026-08-29/persistroute.xclbin
  da64d4b413a1438d27714d5d0b1c0d7e607ca47365849b654873aa5db424447f
build/xclbin/hw_treeseed_2026-08-29/persistroute.xclbin
  323ddd9f3170b8dccc2e76b63661971671da691390ff70984b62ba338cf18c57
```

已完成的最终 `hw_emu` 不要重跑。真实 `diffeq` RR graph 子集已经覆盖四 Search
CU 同 wave 和两轮冲突消解，并与 HBM C-model 五类输出逐字节一致：

```text
projects/persistroute/experiments/accelerated_pathfinder_hw_emu_2026-08-26.json
```

## 5. TilePlace 当前阶段与后续任务

真实前端/correctness、外部 region/fixed 约束、page decomposition、增量 timing/net
cost、macro-aware 冲突协议和主 QoR closure 均已完成。当前主结果是跨两个架构族的九案例
矩阵；apex4 fixed-I/O constrained QoR 作为独立负结果报告，不能并入九例 aggregate。
不能把零移动 CPU golden 当作 QoR 改进。

已完成的 CPU/VPR 研究路径如下，不要回退到从 HLS/Vivado 重新起步：

1. [完成] 编译并运行当前 toy testbench，记录当前接口和确定性行为；
2. [完成] 从冻结的 VTR 9 placement 流中定义真实数据契约：block type、初始/参考坐标、
   fixed/region constraint、CLB/BRAM/DSP site、net/pin、timing criticality；
3. [完成] 实现流式/低内存 packer 和 manifest，保留原始输入 SHA-256、VPR commit、seed、
   channel width 与命令；
4. [完成] 实现不限 512-instance 的 CPU golden，包含异构 site 合法性、唯一占用、区域约束、
   macro/cascade 连续形状与确定性 tie-break；
5. [完成] 将输出写回 VPR placement，并以 VPR placement/route/analysis 做 fail-closed 检查；
6. [完成] 用 `diffeq/frisc/elliptic/clma/koios_conv_layer` 冻结五案例矩阵；
7. [完成] 4×4 page/four-color、touched-net 增量 cost 与 macro-aware site/net 事务探针；
8. [完成] 2×2/q60000 冻结策略、timing guard/page-size 消融、九案例 routed WL/CPD 主矩阵；
9. [完成] apex4 fixed-I/O constrained QoR 独立闭环、六案例 Eigen conventional/AP 强基线、
   六案例 CPU runtime 与 guard-elision 消融；
10. [后续] 优先完成第二个预注册 Titan23 `stereo_vision` 点，但仅可使用冻结哈希匹配的
    Titan 2.0.0 BLIF/SDC；输入仍不可得时继续论文正文、图表和 claim/evidence 整理。
    HBM layout、多 CU/XRT 和 U280 构建不是当前论文成文的前置条件。

TilePlace 的 VPR 9 conventional 与 cluster-level AP 强基线已闭合；DREAMPlaceFPGA、
AMF-Placer 的确切 commit、依赖、命令和格式已冻结为 B1，但方法学审计证明它们不能保持
当前 VPR packed netlist 和 router。若继续，必须另建预注册的外部格式 cohort，在 cohort
内部使用同一输入/约束和后端，报告 routed wirelength、CPD、合法性和端到端时间；没有
本机运行归档前不得登记为 B0。

## 6. Git 与本地数据边界

远端仓库：

```text
https://github.com/GRYYYYYYY/FPGA_Acc.git
branch: main
```

新设备应以 `git log -1` 显示的最新 handoff 提交为准。不要使用
`git clean -fdx`/`git clean -Xfd`：它们会删除被忽略的 Vitis/Vivado、XSim、数据集
和本地实验存档。

GitHub 只包含源码、脚本、论文源文件和紧凑 JSON 证据，不包含：

- `projects/persistroute/build/` 下的 `.xo`、xclbin、Vivado 工程和报告；
- `projects/persistroute/host/.run/` 的 XRT/XSim 现场；
- `projects/persistroute/third_party/` 的 VTR/FPGA24/RapidWright 等下载内容；
- 大型 rr graph、网表、placement/route 工作目录；
- 生成的论文 PDF。

如需在新设备复现 PersistRoute，按 JSON 中的来源、版本和 SHA-256 重新下载/构建，
不要假定缺少被忽略目录表示实验从未完成。

## 7. 原机器状态与清理提醒

交接时原机器为 Ubuntu 22.04.5、kernel `5.15.0-190-generic`、Vitis/Vivado
2022.2、XRT 2.14.354，VMware 未透传 U280；当前没有 Vitis/Vivado/XSim 长作业。

专用 `/var/tmp/persistroute-vivado-16g.swap` 在最新构建后仍处于启用状态。Codex
尝试关闭时因 `sudo` 需要交互密码而未改变系统状态。原机器所有者应在终端执行：

```bash
sudo swapoff /var/tmp/persistroute-vivado-16g.swap
sudo rm /var/tmp/persistroute-vivado-16g.swap
swapon --show
```

执行前再次确认没有 Vivado/Vitis 长作业且 `free -h` 有足够 available memory。
