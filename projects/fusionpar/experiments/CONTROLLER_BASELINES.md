# FusionPAR 分阶段对照与冻结 TP→PR 参考流水线

本阶段把同一 retained-tree 路由器用于分阶段和交错执行，检查此前的改善是否来自
交错调度本身。另重新执行冻结 TilePlace，再从其固定布局启动完整 PR 路由。
这些均为 CPU/C-model 开发实验，不是物理 FPGA 性能结果。

## 控制器对照

三组共用 HPWL 候选生成器、原生 criticality、受影响 net 范围、端点不变的分支
保留规则、PR 内核和原 QoR 门槛。每组的 primary proposal budget 为 3：

- `sequential_tree_reuse`：从初始排名前三的候选中贪心合并不重叠 move，重新加载
  图/状态后路由并原子评估整个 batch。
- `sequential_shared_tree_reuse`：相同 batch 和原子评估，复用已加载图/状态。
- `interleaved_tree_reuse`：逐候选评估；成功后刷新 timing 并重新生成候选。

两个 batch 模式必须具有相同完整状态和事件历史。每个设计每个模式重复五次，
所有结果及失败成本保留。预算代表候选入口，不能将一次 batch 与三次原生验证
当成相同的计算工作；报告实际事件、移动数、最终 QoR 和完整时间。

ex5p 已完成五次：分阶段和交错均得到 WL=9849、CPD=5.83751 ns。分阶段只提交
一次 batch；交错额外拒绝两个候选。cold/shared/interleaved 的 host 中位数分别为
6.018/6.054/12.929 s。这个设计不能把此前改善归因于交错调度。

alu4 已完成五次：两个 batch 模式一次性评估四个 instance move，整体被拒绝，
保持 WL=9580、CPD=5.96812 ns；交错模式每次提交两次、拒绝一次，最终 WL=9548、
CPD 不变。host 中位数分别为 7.318/7.296/15.092 s。这里是更细评估带来的
QoR/时间取舍，不是普遍加速证据。两设计均通过独立状态审计及 cold/shared 等价检查。

协议见 [`sequential_retained_protocol_2026-10-13.json`](sequential_retained_protocol_2026-10-13.json)。
misex3 五次复验均无改善，保持 WL=10323、CPD=5.08031 ns。cold/shared/interleaved
的 host 中位数为 6.813/6.661/13.766 s；每次分别拒绝 1/1/3 个候选。
三设计共 45 次运行，25 次受 QoR 保护的提交、50 次拒绝、70 次 timing barrier。
各模式五次完整状态、事件和 timing 轨迹一致，cold/shared batch 等价，独立审计通过。

| 设计 | cold batch host (s) | shared batch host (s) | interleaved host (s) | interleaved 含公共转换 (s) |
|---|---:|---:|---:|---:|
| ex5p | 6.018 | 6.054 | 12.929 | 15.516 |
| alu4 | 7.318 | 7.296 | 15.092 | 18.221 |
| misex3 | 6.813 | 6.661 | 13.766 | 16.481 |

表内为五次中位数；全部时间样本保留在机器可读索引中。host 时间包含初始验证、
候选原生验证、STA、失败尝试和控制开销，不能直接解释为路由内核或硬件耗时。

## 固定布局全网路由入口

新增 `Engine::prepare_routing()`，显式启动 routing epoch：placement/site 及其版本
保持不变，全部 net 的旧路由在私有副本中释放，调用 PR 后完整验证并原子发布。
普通 `prepare({})` 仍拒绝空 move，不能借此绕过 move 语义。105 项 C++ 检查通过，
包括 route-only 的版本更新、拒绝回退、一次性发布和 native validator 不可绕过。

host 的 `route_only` 模式不生成布局候选。它以原生合法性作为流水线输出条件，
明确标记 `native_legality_only_FIXED_PLACEMENT_PR_BASELINE`；独立审计计入
`baseline_route_commits`，不计入 QoR 改善提交或 protocol_probe。

## TP→PR 复现范围

参考 placer 使用已封存的 TilePlace 实现
`2fa6e2324a971d8489bba12d49115f91d0a56874c0ee5200224d72e4f8a9f689`，核验其
七个源文件后复制到 FusionPAR 输出目录并实际重跑。保留原四个 epoch、24 次
native closure 上限和权重；不修改上游工程。每个设计重跑一次 placer，然后在
该固定输出布局上重复五次 PR。完整当前 placer wall time 计入每次 PR 的 charged
总成本，但这不等于五次完整流水线测量。构建成本另列。

TP 阶段已有 native VPR 路由反馈；其预算和目标也不同于三次 primary 的 FP。
后续需按共同的最终 QoR 条件与总成本比较，不能仅拼接局部计时宣称 FP speedup。
协议见 [`frozen_tp_pr_protocol_2026-10-13.json`](frozen_tp_pr_protocol_2026-10-13.json)。

在读取新 TP→PR 输出之前，还发现 TP 的 native route 遍历顺序与原基线不同。
默认 converter 按此顺序生成 dense ID/PR priority，会额外引入连接排序变量。
稳定身份 `(net, net_pin_index)` 的集合相同，三设计分别有 806/268/1108 个序号位置
不同。已预先记录优先级对齐方案，见
[`pr_priority_alignment_protocol_2026-10-13.json`](pr_priority_alignment_protocol_2026-10-13.json)。
初次 ex5p 接入在初始原生验证时失败，尚未执行 PR：TP 导出的 placement 使用
绝对网表路径，而独立验证目录以 basename 加载网表，VPR 重写文件头导致
Placement_ID 不同。失败保留在 `work/ex5p_frozen_tp_pr_v1`。本地 serializer
规范化网表文件名和 SHA，不放宽身份检查；同一 candidate.state 在修复后通过。
回归及默认输入字节不变的检查见
[`header_priority_regression_2026-10-13.json`](header_priority_regression_2026-10-13.json)。

三个 v2 流水线已完成。ex5p 复用本次会话已成功重跑的 TP 阶段并计入其完整耗时；
alu4/misex3 新执行 TP。三个 TP 最终 placement 文件均复现冻结历史文件的 SHA。
PR 使用稳定 `(net, net_pin_index)` 身份对齐原始 priority，manifest 和实际
`design.txt` 编码均核验；对齐连接数分别为 1916、2331、2365。

| 设计 | TP 原生 WL / CPD(ns) | TP 后全网 PR 的 WL / CPD(ns) | PR 合法重复数 | 共同 2% 门槛通过数 | TP+转换+PR 中位数(s) |
|---|---|---|---:|---:|---:|
| ex5p | 9868 / 5.61423 | 9818 / 6.63478 | 5/5 | 0/5 | 69.152 |
| alu4 | 9561 / 5.96812 | 9630 / 6.80247 | 5/5 | 0/5 | 77.602 |
| misex3 | 10269 / 5.03800 | 10305 / 5.95697 | 5/5 | 0/5 | 115.810 |

15 次 PR 发布均为合法固定布局结果，完整状态和事件重复一致；独立审计记录
15 次 `baseline_route_commits`、0 次 FP QoR 提交、30 次 timing barrier。
全部 CPD 超过原始基线的 102%，因此当前 PR 配置不能提供共同 QoR 条件下的
强参考，不计算 FP 相对这些结果的 speedup。TP 自带原生路由的结果也必须保留：
例如 misex3 的 TP 结果优于当前 FP 初始解，而 FP 尚无接受改善。

后续应分析 PR 搜索代价与原生时序目标的差异，或明确采用已验证 TP routed 解
作为局部 refinement 的起点。不能删除退化结果、放宽门槛，或把额外路由成本
强制加到一个已经得到更好合法解的参考流程上，再据此宣称融合收益。

可复查索引见
[`controller_baselines_status_2026-10-13.json`](controller_baselines_status_2026-10-13.json)，
由 `tools/summarize_controller_baselines.py` 重新审计六套归档、核验冻结 TP 文件、
稳定连接身份及实际 priority 编码后生成。它分别记录 45 次控制器运行和 15 次
固定布局 PR 运行，避免混淆两类发布。

## 全网重路由的时序退化定位

对每个设计 repeat 0 的原生连接延迟作逐连接归因（其余重复已验证状态相同）：

| 设计 | 路径改变的连接 | 延迟增加的连接 | PR 相对 TP 的 CPD 增量(ns) |
|---|---:|---:|---:|
| ex5p | 1748 | 908 | 1.02055 |
| alu4 | 2159 | 1340 | 0.83435 |
| misex3 | 2151 | 1212 | 0.91897 |

所有实例位置不变，初始 criticality 全部非零，排除了误用全零关键度这一解释。
当前图的 edge delay 是 buffered local T_linear / pass-switch local RC 近似，
不是完整原生树负载模型。PR 配置的 `route_tree_timing_weight_q` 默认值为 0，
已有树节点作为搜索 seed 时不计根到该节点的延迟；新扩展边仍按 criticality
计入延迟。一次 PR epoch 内没有新的原生 STA 回调。

这些是代码和记录确认的机制差异，尚不能断言哪一项造成全部 CPD 退化，也不能
断言调整一个权重就能达到门槛。后续时序权重/更新策略必须预先固定并对所有
相关对照一致应用。来源与逐设计完整归因见
[`tp_pr_timing_diagnosis_2026-10-13.json`](tp_pr_timing_diagnosis_2026-10-13.json)。
连接 delay 求和会重复计算共享路径，不能视作 CPD。
