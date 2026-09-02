# TilePlace 独立工程

时序驱动异构页布局 HLS 原型。`tileplace_kernel` 独立处理 CLB/BRAM/DSP page capacity、region、criticality、固定 tie-break 和确定性 site assignment。真实 VPR correctness 路径已支持 VPR direct-chain placement macro 的整体合法化。

普通 C++：`g++ -std=c++17 -O2 -Iinclude src/tileplace.cpp tb/tileplace_tb.cpp -o tileplace_tb`。  
Vitis 2022.2：`vitis_hls -f run_hls.tcl`。

## 当前边界（2026-08-31）

当前代码是独立、可综合的 toy 骨架，不是论文级 placement 系统：固定上限为 512
instances/64 pages，测试只覆盖 8 个合成 instance。该 HLS kernel 尚未计算完整
net/timing 增量，也没有 XRT host 或真实 benchmark 性能数字。

真实 VPR correctness 前端现已独立于 HLS kernel 建立：

- `tools/capture_vpr_macros.py` 由同一 VPR revision 从 architecture directs 与 packed
  netlist 连接导出并校验 `place_macros.echo`；
- `tools/tileplace_vpr.py pack` 流式读取 packed `.net` 与 RR graph，读取 `.place`、
  connection/timing CSV 和 VPR 原生 macro，输出带输入/输出 SHA-256 的 JSONL contract；
- `tools/prepare_reference_timing_input.py` 确定性生成 patched-VPR timing 输入；可选映射
  exporter 对无 atom timing-pin 对应的 routed connection 显式写
  `timing_pin_mapped=0`/criticality 0，不静默丢行；
- `legalize` 是不受 512-instance 限制的确定性 CPU golden，覆盖异构 site、subtile
  唯一占用、region、fixed block 和 macro/cascade 相对形状；
- `validate` 对 block 完整性、site/type、唯一占用、region、fixed 和 macro 做
  fail-closed 检查，并写出标准 VPR `.place`；
- `pack --vpr-constraints` 直接读取 VPR 原生 XML，按精确 atom 名优先、regex search、
  atom→cluster 和同 cluster 多 partition 交集语义导入 region 并集、layer、subtile 与
  部分 fixed 维度；
- `tests/test_tileplace_vpr.py` 包含 600-block、异构/fixed/region/cascade、VPR macro
  orientation、重复占用拒绝、逐 connection endpoint 与同 tile 多 IO subtile 消歧测试。

五案例 correctness matrix 位于 `experiments/correctness_matrix_2026-08-31.json`：共
2866 个 clustered blocks 和 47580 条 routed connections，全部 CPU golden 与 VPR
原生 route+analysis 合法，routing iterations、wirelength、CPD 均与冻结 baseline
一致。Koios `conv_layer` 含 822 CLB、42 DSP、56 memory、156 IO；VPR 从 carry direct
链识别 43 个 placement macro/86 个成员，contract 与 closure 再生 macro 哈希一致。

精确 VTR commit `8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07` 已以 VPR-only
Release/`VTR_ASSERT_LEVEL=2` 构建。`tools/run_vpr_closure.py` 将 golden 复制到隔离
work 目录后运行串行 route+analysis，要求 placement/routing consistency 与全部成功
标记同时存在，并核对归档 golden 未被 VPR 改写、VPR 再生 macro 哈希不变。Koios
非法输入注入重复占用、CLB/DSP 互换和 memory 非 root offset 后，CPU legalizer 两次
确定性恢复相同结果（从输入移动 15 个 block），恢复 placement 再通过 VPR 原生
placement/routing consistency、14 轮布通和 analysis。该矩阵证明 correctness，不是
新的 placement QoR 提升或硬件性能结果。

外部约束矩阵 `experiments/external_constraints_matrix_2026-08-31.json` 冻结 VTR
regression 自带的 `bigkey_tight.xml` region 与 `apex4_io_constraint.xml` fixed-I/O
案例，共 686 blocks、252 matched atoms、176 constrained clusters，其中 28 个为
x/y/layer coordinate-fixed。两例参考布局、同类型违规交换、两次确定性 CPU 恢复和
VPR 原生重读 XML 后的 route+analysis 均通过。该约束矩阵生成时使用的冻结 VPR binary
未链接 Eigen，故其中 passing fixed-I/O 案例仍只是常规 VPR placer 约束闭环；后续独立
Eigen-enabled build 没有重跑或替代这份约束证据。
在结果产生前又将 apex4 单独预注册为 constrained post-freeze QoR 点，以最终
2×2/q60000 策略运行。2,263/2,263 条 connection 同时映射 clustered endpoints 与 atom
timing pins，两次 CPU 输出逐字节一致，28 个 coordinate-fixed I/O 保持；原生 WL/CPD
10023→10044（+0.210%）/5.20192→5.22600 ns（+0.463%），19→21 routing iterations。
该负结果见 `experiments/constrained_qor_matrix_2026-09-01.json`，只证明约束兼容的 QoR
闭环，不并入九例 unconstrained aggregate 或六例 Eigen AP 表。

首个算法探针 `experiments/page_incremental_probe_2026-08-31.json` 已实现 4×4 page
decomposition/四着色、受影响 net 的精确增量 HPWL/逐 connection timing cost，以及以
old/new site write-set 和 touched-net set 为冲突边界的确定性提交；VPR macro 作为不可
拆分事务。Koios 两次运行逐字节一致，43 macros 保持，routed WL
`232357→231991`（-0.158%）、CPD 保持 5.12784 ns；`bigkey_tight` routed WL
`11415→11416`，故拒绝该点。

九个 QoR endpoint contract 共 198595 条 routed connections，全部映射到 source/sink
clustered block；IO SINK 由 RR class stride 消歧 subtile，Koios DSP/memory 的 RR endpoint
按多高度物理 tile footprint 映射回 placement root。
消融 `experiments/timing_guard_ablation_2026-08-31.json` 证明 net-max×HPWL 和未保护的
connection-star 均会使 diffeq CPD 回归，而输入相对的高关键连接距离 guard 可消除该
退化。2×2/4×4/8×8 page 消融在四例开发集上选择 2×2；冻结 q60000 策略先形成六例矩阵
`experiments/timing_multicase_matrix_2026-08-31.json`，再以完全相同参数加入 attention_layer，
七案例严格 timing-export 扩展见 `experiments/timing_extended_matrix_2026-08-31.json`；
另以最终策略复验此前出现于 4×4 macro probe 的 conv_layer，形成八例历史基矩阵
`experiments/timing_macro_extended_matrix_2026-08-31.json`；随后不改 2×2/q60000 策略，
在第二架构族加入 Titan23 neuron，形成九例矩阵
`experiments/timing_titan_extended_matrix_2026-09-01.json`。串行 VPR route+analysis 的
routed WL/CPD 几何平均为 -0.088%/-1.010%；最坏单例 +0.439%/+0.017%，5/9 案例 WL
改善、8/9 CPD 不回归。冻结后验证的 spmv/softmax/attention_layer/Titan23 neuron 单独为
WL -0.015%、CPD -2.236% geomean；Titan23 neuron 诚实保留 WL +0.088%、CPD 不变和
15→16 routing iterations。conv_layer 保持 43 macros/86 members，WL -0.124%、CPD 不变，
但因曾参与早期 probe，不标为 post-freeze。九例的 198595 条 connection 均映射 clustered
endpoints；194155 条映射 atom timing pin，conv_layer 的 4440 条显式标为 unmapped、
criticality 置零但保留在线长目标。输入 provenance 见
`experiments/{attention_layer,conv_layer}_input_capture_2026-08-31.json` 与
`experiments/titan23_neuron_input_capture_2026-09-01.json`。逐事务 HPWL
不增的 wire0 消融仍只属于四例开发集且受支配，故不设为默认。
这是 CPU placement+VPR QoR 证据，不是 U280 性能结果。

同 packed-netlist 强基线见
`experiments/vpr_placement_baseline_matrix_2026-08-31.json`。精确 VTR revision 使用
Eigen 3.4.0 构建为独立 VPR binary（SHA-256
`dd7d30f7faf133fa2ee2196a0b307aa2784e60398a7356d209364a39a16b6508`）；runner 显式执行
`--place --route --analysis`，以 `--enable_analytic_placer false/true` 配对 conventional
SA 与 cluster-level AP + quench，并禁止 integrated `--analytical_place`。六个
conventional 点精确复现冻结 baseline；AP 六例全合法，但相对 conventional 的 WL/CPD
geomean 为 +3.711%/+16.103%，0/6 改善 WL、0/6 CPD 不回归。该 AP 是 VPR 官方实验性
wirelength-oriented 路径，不等价于外部 timing-driven placer；单次 VPR 时间不作性能 claim。

外部 placer 可行性审计见 `experiments/external_placer_feasibility_2026-08-31.json`：
DREAMPlaceFPGA `004494318...` 与 AMF-Placer `70d982881...` 的 license、源码、CLI、依赖和
输入/输出均已固定为 B1 executable-source candidates。DREAMPlaceFPGA 会从 flat
Bookshelf/FPGAIF 输入重新 packing/legalization；AMF-Placer 使用 Vivado 提取的 primitive/device
数据并回灌 Vivado Tcl。两者都无法保持当前 VPR packed netlist、architecture 和 router，故未
强行构建，也不能写入九例 TilePlace 同 router 表；B0 复现必须另建清楚分离的外部格式实验。

单核 Python reference 固定 CPU 31、3 次 warm-up 与 7 次 measured run，完整计入 contract
读取、优化、`.place` 写出、合法性验证和 JSON 报告。六案例中位数为
0.545/1.513/1.581/4.052/59.672/21.798 s；合并结果见
`experiments/cpu_runtime_sixcase_matrix_2026-08-31.json`，新增两例原始样本见
`cpu_runtime_validation_matrix_2026-08-31.json`。四例开发集消除禁用 wire guards 的无效 before-cost
得到 1.439× geomean speedup（逐例 1.338×--1.649×），placement 哈希不变；elliptic
wall-time CV 为 15.0%，因此只报告中位数及完整样本。Linux fork-process proposal 路径在
四案例 1/2/4/8 workers 下与串行的目标、冲突计数、逐 pass 和 placement 哈希完全一致，
但受控 clma 中位数 4.046/4.112/4.190/4.104 s，没有并行 speedup。该路径只证明并行
语义，不能写成 scalable CPU 或 FPGA 加速。

## CPU correctness

```bash
python3 -m unittest discover -s tests -v

python3 tools/tileplace_vpr.py pack \
  --netlist <design.net> --place <design.place> --rr-graph <rr_graph.xml> \
  --architecture <arch.xml> --native-macros <place_macros.echo> \
  --connections <connections.csv> --timing <timing.csv> \
  --output <contract_dir> --vpr-revision <revision> \
  --seed 1 --channel-width 200 --vpr-command '<exact VPR command>'

# 也可用原生 XML；它与 --constraints JSON 互斥
python3 tools/tileplace_vpr.py pack ... \
  --vpr-constraints <vpr_constraints.xml>

python3 tools/tileplace_vpr.py legalize \
  --contract <contract_dir> --output <design.golden.place> --report <golden.json>
python3 tools/tileplace_vpr.py validate \
  --contract <contract_dir> --place <design.golden.place>

python3 tools/run_vpr_closure.py \
  --contract <contract_dir> --vpr <vpr> --architecture <arch.xml> \
  --circuit <design.blif> --netlist <design.net> \
  --golden-place <design.golden.place> --work <isolated_work_dir> \
  --report <native_closure.json> --seed 1 --channel-width 200

python3 tools/run_vpr_placement_baseline_suite.py \
  --config experiments/vpr_placement_baseline_cases_2026-08-31.json \
  --workspace-root ../.. --work-root work \
  --report-root experiments/vpr_placement_baselines_2026-08-31 \
  --runner tools/run_vpr_placement_baseline.py --resume

python3 tools/prepare_vpr_placement_baseline_matrix.py \
  --config experiments/vpr_placement_baseline_cases_2026-08-31.json \
  --reports experiments/vpr_placement_baselines_2026-08-31 \
  --build-provenance experiments/vpr_eigen_build_2026-08-31.json \
  --tileplace-matrix experiments/timing_multicase_matrix_2026-08-31.json \
  --output experiments/vpr_placement_baseline_matrix_2026-08-31.json
python3 tools/prepare_constrained_qor_matrix.py \
  --output experiments/constrained_qor_matrix_2026-09-01.json
```

可选 constraint JSON 的字段为 `fixed` block-name 列表、`regions` 映射（每项为
`[xmin,ymin,xmax,ymax]` 或追加 layer），以及 `macros` 列表。每个 macro member 声明
`block/dx/dy/dsubtile/dlayer`，同一机制用于表达 cascade 连续形状。

## 接手后的实现顺序

1. [完成] 增加真实 region/fixed 外部约束案例；
2. [完成] page decomposition、2/4/8 page-size 消融、增量 net/per-connection timing
   cost、critical-distance guard 与 macro-aware 并行冲突协议已有确定性 CPU 实现及
   九案例、两个 architecture families 的统一 router 矩阵，其中四例为策略冻结后验证、一个为 previously-probed
   macro-stress；
3. [完成] conventional VPR 与官方 cluster-level AP 已在六例同 packed netlist/router 下闭环；
4. [进行中] 继续扩展 post-freeze VPR/Koios 案例；DREAMPlaceFPGA/AMF-Placer 已完成 B1
   source/CLI/format 审计，但需另建 Bookshelf/FPGAIF/Vivado cohort 才能做有效比较。当前
   单核 runtime 已闭合，Python process scaling 受支配；
5. 算法 correctness/QoR 冻结后再扩展 HBM ABI、多 CU/XRT、HLS/RTL 和 U280 实现。

VPR conventional/AP 强基线现已可执行。DREAMPlaceFPGA、AMF-Placer 的 commit、依赖与
命令已经固定，但格式审计表明它们不能直接使用当前 VPR 后端；只有独立预注册并完成本机
合法性/QoR 归档后才能从 B1 升为 B0，且不得与九例 TilePlace QoR 矩阵混表。
