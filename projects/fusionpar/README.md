# FusionPAR 独立工程

本工程已建立供 TP/RC 后续接入的 C++ move–route 联合事务框架。首先从合法
VPR placement + routing 启动局部 refinement，接入 PersistRoute production HBM
C-model，并以原生 VPR 检查作为发布候选的前置条件。逐项验收及后续研究边界见
[`experiments/FRAMEWORK_ACCEPTANCE.md`](experiments/FRAMEWORK_ACCEPTANCE.md)，
机器可读计划见 [`experiments/framework_plan.json`](experiments/framework_plan.json)。
TP/RC 接入、Sketch 调用时的状态含义、PR 分支占用以及串行提交范围见
[`experiments/FRAMEWORK_CONTRACT.md`](experiments/FRAMEWORK_CONTRACT.md)。

首轮 25 次真实运行和独立审计见
[`experiments/FRAMEWORK_RESULTS.md`](experiments/FRAMEWORK_RESULTS.md)：协议成功提交与
拒绝均可复现，该首轮阶段的研究模式没有接受改进。
新增失败反馈与布局修复已通过 79 项 C++ 检查；ex5p/alu4/misex3 的另 25 次开发
运行和 21 次额外布局修复均已独立审计，该布局修复阶段无 QoR 接受提交。汇总见
[`experiments/placement_repair_status_2026-10-13.json`](experiments/placement_repair_status_2026-10-13.json)。


分支保留实现及开发证据见
[`experiments/TREE_REUSE_RESULTS.md`](experiments/TREE_REUSE_RESULTS.md)。97 项 C++ 检查
已通过；修复 I/O 导出格式后的 18 次开发运行及独立审计通过，ex5p、alu4 得到受
原 QoR 门槛保护的可重复改善，misex3 没有改善。

后续同路由器分阶段对照及冻结 TP→PR 结果见
[`experiments/CONTROLLER_BASELINES.md`](experiments/CONTROLLER_BASELINES.md)：45 次控制器
运行与 15 次固定布局 PR 运行已完成。ex5p 分阶段得到相同 QoR 且更快；alu4 交错
改善线长但耗时更多；misex3 无改善。TP→PR 全量重路由均原生合法，但 CPD 超过
共同门槛，不能据此计算同等质量的加速比。框架已有 105 项 C++ 检查通过。

最新等候选评估预算的反馈对照见
[`experiments/FEEDBACK_BUDGET_RESULTS.md`](experiments/FEEDBACK_BUDGET_RESULTS.md)：
三个设计、两种策略各五次，共 30 次九候选运行已通过确定性和独立状态/预算
审计。ex5p、misex3 两组最终质量相同；alu4 反馈组线长更低、CPD 略高。
85 次 QoR 提交、185 次拒绝及 60 次修复均归档，尚无普遍融合优势。

路由树前缀时序权重与原生验证开销的后续诊断见
[`experiments/TREE_TIMING_COST_RESULTS.md`](experiments/TREE_TIMING_COST_RESULTS.md)。
113 项 C++ 检查、54 次真实运行及全部独立审计通过，权重零完整复现旧语义。
完整前缀计价降低了全网 PR 的 CPD，却使线长超限；控制器结果也因设计而异，
默认权重仍为零。132 份 adapter 成本记录显示重复 RR XML 解析占记录 body 的
35.04%，可作为后续公共转换缓存的优化对象；不据此宣称 FPGA 性能收益。

RR 导出缓存现已完成 60 次配对运行：90 对原生验证的 630 项文件比较字节一致，
状态、事件和时序轨迹保持不变。缓存降低 host 时间，但首次准备使短 batch 总
时间增加，默认仍为 XML。结果见
[`experiments/RR_EXPORT_CACHE_RESULTS.md`](experiments/RR_EXPORT_CACHE_RESULTS.md)。
共同最终目标下的 TP 强参考及 75 个布局审计见
[`experiments/TP_CHECKPOINT_REFERENCE.md`](experiments/TP_CHECKPOINT_REFERENCE.md)：
最佳已访问可行候选均曾被 TP 自身策略拒绝，不能只用 TP 最终输出代表强基线。
随后 15 次九闭合预算 TP 重跑与 135 个原生候选审计通过，和 FP 九候选结果使用
相同初始状态及最终目标比较：TP 在 ex5p/misex3 上线长更低，FP 在 alu4 上更好。
这不构成普遍融合优势或配对加速证据。

其余六设计的冻结独立输入验证已完成全部 12 组尝试，结果见
[`experiments/INDEPENDENT_VALIDATION_RESULTS.md`](experiments/INDEPENDENT_VALIDATION_RESULTS.md)。
apex2/des/seq/spla 完成 80 次 host 运行和八份独立发布审计，合计 35 次受 QoR
门槛保护的提交、405 次拒绝、105 次修复。s38584.1/tseng 均因未支持的根时钟
在转换阶段拒绝，覆盖为 **4/6**，不是六设计全部通过。九次等评估预算下，现有
反馈策略在三个设计上最终线长更差、一个持平；三个 primary 的分阶段/交错
对照均没有改善质量。本轮不支持普遍融合收益，反馈仍为显式实验模式。
预登记协议保持原始字节，完成状态以结果报告和原始 study 为准。

## 构建与协议回归

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j 8
ctest --test-dir build --output-on-failure
```

不需要 Xilinx 工具或板卡。构建直接编译相邻 PersistRoute 工程的 production
C-model 源文件，不修改它们。`fusionpar_joint_tb` 实际调用其搜索/提交/多 sink 树
控制层，验证端点重映射、旧分支释放、共享占用、原子发布、过期事务、timing
barrier、原生验证拒绝、损坏路径、版本溢出、swap/macro/fixed 约束及有界 repair。
另有五次重复运行的语义状态校验。
当前 CTest 3/3 通过，包含 113 项 C++ 联合状态检查及 6 个 Python 缓存测试。

## C++ 状态与事务

接口在 [`include/joint_state.hpp`](include/joint_state.hpp)，实现位于
[`src/joint_state.cpp`](src/joint_state.cpp)。

- `Design` 保存 CSR 图、site pin→RR terminal 映射、实例允许位置、macro 和连接身份。
- `State` 保存 placement/site/route/resource 版本、完整路径、criticality snapshot 和 epoch。
- `prepare` 在私有副本上改变位置、重映射端点、释放受影响 net 的整个树并调用 PR。
  不受影响 net 的资源占用保持保留。多 sink 共用节点按 **net** 计一次占用。
- candidate 由独立的 FP 路径/树/容量检查、可选原生 validator、接受策略依次检查。
  成功后 `commit` 统一发布 placement 和 routing；任何失败都丢弃 candidate。
  显式启用 `retain_branches` 时，端点不变的分支保持完整路径和 route 版本，由
  [`src/retained_router.cpp`](src/retained_router.cpp) 在私有工作区重建保留树并搜索其余连接。
- v1 在单线程控制面校验整个 immutable snapshot/revision 和 timing epoch。
  这是保守的串行化协议，尚未实现无交集事务并发提交。
- PR 的中间 occupancy、版本和 negotiated-congestion costs 仅在私有工作区使用。
  FP 发布前重新统计占用；每个涉及的资源版本恰加一，包括占用数量不变的路径替换。
  片内 source 不计入 occupancy，与 PR 的 source-excluded path ABI 相同；原生工具
  负责进一步核验完整器件合法性。
- timing barrier 只接受绑定当前 revision 的完整 criticality 数组，更新后使旧候选失效。
  bundle 配置 `--timing-vpr` 时，host 在初始状态和每次成功提交后消费原生 STA 的
  完整 criticality 数组；每次 barrier 的来源和前后状态记录在 `timing.jsonl`。

PR adapter 在调用会使用饱和算术的上游 kernel 前检查保守的代价范围上界，遇到
16-bit 代价极限、32-bit 路径代价风险或版本极限时拒绝该候选。该检查可能保守地
拒绝可路由候选，其失败和重试成本必须计入结果。

`Router`、`Sketch`、`Validator`、`Acceptance`、`Repair` 是独立接口。默认 sketch
不启用；`run_proposal` 提供有限 repair 次数和重复候选抑制。host 的
`interleaved_repair` 在局部 routing 失败后最多尝试一次全网重路由。
新增 `interleaved_placement_repair` 使用失败连接定位相关的已移动实例，在原失败
移动的距离范围内选择其他合法 move/swap，每个失败 primary 最多尝试两个修复。
原生 delay 增加的连接按原 criticality、delay 增量和连接 ID 排序；没有 delay
增加时使用 net 的实际 RR wire 增长。路由失败则消费 PR 的未完成/拥塞连接反馈。
候选仍通过同一原生检查和 QoR 门槛，不递归修复，不重复完整 placement。
策略实现在 [`src/joint_repair.cpp`](src/joint_repair.cpp)，目前仍枚举并排序全部合法
move/swap；成本计入 host 时间，不能视作高效局部搜索实现。

## 真实 VPR 开发实验

[`tools/prepare_vpr_bundle.py`](tools/prepare_vpr_bundle.py) 将已有合法 `.net/.place/.route`
和 PR graph arrays 转成 C++ 输入。复用 TP placement contract 和 RC 的 pre-route
pin-class 映射器，绑定输入和源码 SHA-256。当前 converter 限制为单 layer、可直接
映射 logical/physical pin name 的器件；遇到未支持的根时钟不会静默省略。

[`tools/validate_candidate.py`](tools/validate_candidate.py) 在独立目录输出 `.place/.route`，
检查 TP region/fixed/macro 约束、重新统计资源 owner，并调用 PR 的 VPR native checker。
候选必须通过 placement consistency、routing consistency、可行性和 STA。`.place`
必须与 VPR `print_place` 格式一致，否则加载时重写会改变 route header 的身份。
不修改上游输入，不放宽 Placement_ID 检查。

host 用法：

```bash
./build/fusionpar_host BUNDLE OUTPUT MODE ATTEMPTS tools/validate_candidate.py [TREE_TIMING_WEIGHT_Q]
```

`OUTPUT` 必须是新目录。开发模式为：

| 模式 | 行为 |
|---|---|
| `sequential` | 先生成合法不重叠 move batch，再重新加载图/状态，对全部 net 路由 |
| `sequential_shared` | 相同 batch 和全部 net 路由，复用已加载图/状态 |
| `interleaved` | 每次候选只重路由受影响 net，提交后重新生成候选 |
| `interleaved_repair` | 局部路由失败时额外允许一次全网路由 repair |
| `interleaved_placement_repair` | 根据失败连接，尝试最多两个有距离限制的替代布局 |
| `interleaved_tree_control` | 新树控制器从空树重建，对照原 PR 事件与搜索语义 |
| `interleaved_tree_reuse` | 同一控制器保留端点不变的完整分支，搜索其余连接 |
| `sequential_tree_reuse` | 同一分支保留路由器评估不重叠 move batch，重新加载图/状态 |
| `sequential_shared_tree_reuse` | 相同 batch 和路由器，复用已加载图/状态 |
| `interleaved_tree_feedback` | 与 tree reuse 共用总评估预算，优先尝试最多两个失败反馈驱动的替代布局 |
| `route_only` | 固定 placement 的全网 PR 路由；仅作原生合法性参考，单独计数 |

接受策略固定为 native `(wirelength, CPD)` 严格字典序改善，且 CPD/WL 不超过初始
合法解的 102%。候选由简单的合法 move/swap 生成器按受影响 net 的 HPWL delta
确定性排序。它们是开发控制策略，不代表最佳布局算法。内部测试可显式使用
`--internal-only` 替代 validator，此时只检查图/状态和严格 wire-unit 改善，不能
作为 VPR 原生合法性证据。

额外的 `protocol_probe` 模式只要求原生合法性，用于验证成功发布和发布后的 timing
反馈。它的接受策略在 summary 中明确标记为 `native_legality_only_PROTOCOL_TEST`，
与受 QoR 保护的研究模式分别计数；其结果不能进入收益比较。

[`tools/run_development.py`](tools/run_development.py) 从源码重新构建，保存源码副本、
测试日志、转换 manifest、每次事件、候选原生检查及最终状态。四种模式轮换执行顺序，
默认每种重复五次。检查每种模式最终状态 SHA-256 和事件语义一致，以及 cold/shared
顺序模式结果一致。失败尝试和全部 native 检查进入 subprocess wall time；输入转换
作为公共成本单列，并等额加入每种模式的 charged wall time。

增加 `--timing-vpr /path/to/patched-vpr` 可启用 timing 闭环：保留候选原生 RC 树的
delay，不用 PR 的局部 edge-delay 近似覆盖它；导出全部连接 criticality，并要求
导出器 CPD 与独立 native STA 的打印值在 1 ps 内一致。缺失/重复连接、缺失输出、
CPD 不一致均失败。`--protocol-probe` 在四种研究模式之外附加成功提交协议测试。
`--placement-repair` 额外启用布局修复模式，原生每连接 delay 及其文件 SHA-256
一并归档；事件记录父候选、move、反馈连接和候选状态摘要。
`--tree-reuse` 附加空树/分支保留两种模式；记录保留连接 ID 和实际 kernel 搜索次数，
并要求空树模式复现原 PR 的事件语义。
可用 `--modes interleaved interleaved_tree_control interleaved_tree_reuse` 显式运行
聚焦对照；未运行的 cold/shared 对照标记为 `null`，不会算作通过。

`interleaved_tree_feedback` 的 `ATTEMPTS` 是 primary 与 repair 合计的评估上限。
与 `interleaved_tree_reuse` 同预算配对时，runner 额外记录实际评估数是否均达到
上限；候选耗尽不能冒充等次数对照。协议见
[`feedback_budget_protocol_2026-10-13.json`](experiments/feedback_budget_protocol_2026-10-13.json)。
原 `interleaved_placement_repair` 仍使用 primary 预算外追加修复的历史语义。

host 可选的 `TREE_TIMING_WEIGHT_Q`，或 runner 的 `--tree-timing-weight-q`，
接受 0..256 的 Q8 值，默认 0；256 计入完整的近似已有树前缀延迟。所有模式使用
同一参数，host summary、执行命令和 suite receipt 的一致性由独立审计检查。
每次原生验证新增 `costs.json`，记录不重叠的 adapter 阶段耗时；没有关闭检查。

runner 和 converter 可选 `--rr-export-backend sqlite`（默认 `xml`），在准备阶段
生成只读 RR 导出元数据，并对完整导入 CSR 与 XML 做往返检查。缓存绑定图、CSR
和实现 SHA；每次原生验证前后继续核验文件。身份不符、缺失节点/边或使用歧义
switch 均拒绝。首次建库与完整校验费用计入 charged time，不作为 FPGA/HBM
接口或 FusionPAR 独立算法贡献。

`--priority-reference BUNDLE/manifest.json` 按稳定 net/pin 身份绑定 PR priority，
用于改变 placement 后的同连接顺序对照；缺失身份或网表 SHA 不同均拒绝。
[`tools/run_tp_pr_baseline.py`](tools/run_tp_pr_baseline.py) 复现冻结 TP 实现并连接
`route_only`，保留合法但不满足共同 QoR 门槛的输出及完整费用。

```bash
python3 tools/run_development.py \
  --case-root /path/to/ex5p-case --design ex5p \
  --vpr /path/to/vpr --arch /path/to/architecture.xml \
  --circuit /path/to/ex5p.blif --channel-width 200 \
  --output work/ex5p-development --attempts 3 --repeats 5
```

[`tools/audit_development.py`](tools/audit_development.py) 可再次独立重建全部发布和
timing barrier，检查 placement/site/route/resource 的版本变化、失败不改状态、
native 证书、研究模式 QoR 条件以及最终完整状态：

```bash
python3 tools/audit_development.py work/ex5p-development \
  --output experiments/ex5p_publication_audit.json
```

case 目录当前需包含 `baseline/{ex5p.net,ex5p.place,ex5p.route,rr_graph.xml}` 和
`inputs/{vpr_input.manifest.json,vpr_input.nodes,vpr_input.edges,vpr_input.resources,contract/}`。

## 证据边界

- 该框架的真实入口是已有合法 routed design，尚不支持从 packing 后输入开始的完整 P&R。
- 未配置 `--timing-vpr` 的实验冻结 criticality=0。配置后在事务边界刷新，单次 PR
  搜索内部仍使用固定 snapshot；两类实验不能混作同一算法的结果。
- 当前对照是相同简单 move 生成器的分阶段/交错执行，尚不是“最佳 placer + PR”。
- `copy_payload_bytes` 只统计 FP 的显式逻辑 payload 复制，不含 PR 内部所有分配，也不是
  实测 PCIe/HBM 流量。`routing_ns` 包含 PR CPU scratch allocation、搜索和私有提交。
- 严格状态回退、原生合法性和 CPU 计时都不能证明板上性能。此处没有物理 U280 结果。
- TP 已有 routed-oracle move/rollback；FP 需进一步证明共享状态和跨阶段控制减少返工的
  独立净收益，不能把组件复用或普通 rollback 再次当作贡献。

## 早期 HLS 原型

原 `fusionpar_kernel` 保留为固定上限的资源增量原型，**没有**完整 placement state、
timing epoch、路径生成或真实 repair 闭环。它现已合并同资源 delta 后再检查容量，并
对每个资源只递增一次版本；不能把这一修复解释为完整联合事务协议已经硬件化。

```bash
g++ -std=c++17 -O2 -Iinclude src/fusionpar.cpp tb/fusionpar_tb.cpp -o /tmp/fusionpar_tb
# 加载 AGENTS.md 指定工具环境后才可运行：
vitis_hls -f run_hls.tcl
```

本轮未运行 HLS/RTL 验证。后续在真实事务 footprint 和完整成本归因稳定后，再决定
transaction pool、HBM ABI、部分树复用和硬件并发的实现顺序。
