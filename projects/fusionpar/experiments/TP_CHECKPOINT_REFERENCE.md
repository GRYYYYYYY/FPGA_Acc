# FusionPAR 共同最终目标下的 TP 已访问强参考

只比较 TP 最终输出会漏掉被 TP 自身时序优先策略拒绝、但符合 FusionPAR
线长优先目标的候选。本阶段完整检查冻结 TP 每个设计实际执行的 24 次原生
闭合，加上初始合法状态，共 75 个状态；没有重新布线或改写 TP 最终结果。

统一选择规则为：原生合法，WL 和 CPD 均不超过原始 routed baseline 的 102%；
在所有符合门槛的状态中最小化 `(WL, CPD, trial)`，初始状态编号为零。
TP 接受和拒绝的候选都进入总体。协议和结果分别见
[`tp_checkpoint_reference_protocol_2026-10-13.json`](tp_checkpoint_reference_protocol_2026-10-13.json)、
[`tp_checkpoint_reference_status_2026-10-13.json`](tp_checkpoint_reference_status_2026-10-13.json)。

| 设计 | 所选 trial | WL | CPD(ns) | TP 自身接受？ | 符合共同门槛的 trial | 完整 TP 调用(s) |
|---|---:|---:|---:|---|---:|---:|
| ex5p | 5 | 9752 | 5.88248 | 否 | 24/24 | 57.943 |
| alu4 | 20 | 9531 | 5.97476 | 否 | 24/24 | 62.267 |
| misex3 | 20 | 10189 | 5.13863 | 否 | 18/24 | 100.331 |

72 个 trial 都原生合法；misex3 有六个不符合共同质量门槛。三个所选状态都曾被
TP 自身策略拒绝，因此不能把它们称为 TP 原算法的最终输出。它们是这条已执行
轨迹中、按 FP 最终目标选出的最佳可行状态，也不等价于每步使用 FP 接受策略
重新运行 TP。

相较原三个 primary 的 FP 结果，表中 TP 参考在三个设计上线长均更低，CPD 有
相应取舍。24 次与三次或九次预算不同，不能据此声称等预算优势。每个参考保留
完整 24 次执行费用，即使所选候选很早出现，也不把历史总时间截断为前缀时间。

## 原生与契约核验

选择器核对冻结实现、全部 trial/closure 数量、输入输出 SHA、VPR 原始日志中的
合法性和质量、packed netlist 身份以及 route 的 Placement_ID。
补充审计重新检查 75 个原生布局的共同 site/type/region/fixed/macro 契约，并对
72 个候选核对输入与原生输出的全部实例坐标、layer 和 block ID。结果见
[`tp_checkpoint_contract_audit_2026-10-13.json`](tp_checkpoint_contract_audit_2026-10-13.json)。

审计实现曾把 `placement_validation.placement_sha256` 误与输入 proposal 比较。
冻结 `run_vpr_closure.py` 在路由结束后对 canonical VPR 输出生成该证书，因此
正确绑定对象是 `outputs.vpr_place_copy`；输入候选单独做 SHA 和坐标一致性检查。
修正后全总体通过。两个一次性副本负例分别破坏证书哈希与输入 block ID，均在
对应检查处拒绝，见
[`tp_checkpoint_auditor_regression_2026-10-13.json`](tp_checkpoint_auditor_regression_2026-10-13.json)。

## 成本口径澄清与后续

原协议和选择器结果的 limits 中把 initial feedback 写为 reused/not remeasured，
这一表述不准确：冻结入口在计时的 TP 调用内执行 `prepare_feedback` 和
`prepare_timing_feedback`，其费用已包含。实际复用、未重新测量的是初始原生
布局/路由/时序报告、RR 图和契约的生成。这一澄清保留原始协议及结果字节不变，
避免破坏既有证据哈希；不改变任何质量、选择或已记录调用时间。

后续已采用真实的九次闭合上限，分别重新执行五次，并按上述共同最终规则选择
参考。预先记录的协议见
[`tp_budget_reference_protocol_2026-10-13.json`](tp_budget_reference_protocol_2026-10-13.json)。
这样只对齐候选评估次数；TP 批量移动、原生路由与 FP 局部移动、PR 增量路由的
工作量仍不同。内部接受目标也不同。开发集已被反复检查，仍需冻结策略后的
独立验证集合；不能把这些参考整理结果当作普遍融合优势。

## 九次闭合预算的真实重跑

`tools/run_tp_budget_reference.py` 在 FusionPAR 内复制并核验冻结 TP 源码，只把
`--max-closures` 从 24 改为 9。每次启动全新的 TP 子进程，重复间轮换设计顺序。
15 次运行全部实际消耗九次闭合；测量结束后检查 135 个候选及 15 个初始状态，
核对原生日志、SHA、布局契约、坐标、路由身份。全部候选原生合法。
五次的完整候选事务、坐标、路由正文、质量和接受结果均一致。

最终选择与已有九候选 FP 的比较见
[`tp_budget_reference_status_2026-10-13.json`](tp_budget_reference_status_2026-10-13.json)。
两者初始 net/place/route 的 SHA 相同；三个设计使用同一个最终选择规则，没有
针对不同设计挑选目标或时序权重。

| 设计 | TP 所选 trial | TP 最佳已访问 WL / CPD(ns) | FP 盲选 WL / CPD(ns) | FP 反馈 WL / CPD(ns) |
|---|---:|---|---|---|
| ex5p | 5 | 9752 / 5.88248 | 9844 / 5.83751 | 9844 / 5.83751 |
| alu4 | 8 | 9535 / 5.97476 | 9510 / 5.93739 | 9485 / 5.96812 |
| misex3 | 6 | 10262 / 5.14741 | 10319 / 5.08031 | 10319 / 5.08031 |

所选 TP 候选仍均被其内部时序优先策略拒绝；每次 ex5p/alu4 的九个候选均符合
共同门槛，misex3 为七个。按共同线长优先规则，TP 在 ex5p/misex3 上更好，FP
在 alu4 上更好；前两者的 FP 有更低 CPD。alu4 两个 FP 模式均在 WL 和 CPD 上
优于所选 TP 九预算参考，但反馈与盲选之间仍有原来的 WL/CPD 取舍。

完整 TP 调用的五次中位数分别为 24.139、22.249、39.768 秒。每次都实际运行
九次闭合，这些数值不是从 24 次总费用按比例折算。调用内包含初始反馈、候选
生成、全部原生路由/分析、成功后反馈刷新、失败和输出；选择及独立审计在测量
后另计。已有 FP 测量来自另一批运行，CPU affinity 也不同，不据此计算加速比。

该实验补齐了共同最终目标与九次候选评估预算的开发强参考。TP 内部接受规则、
批量移动和路由工作量仍与 FP 不同，所以不能声称在线搜索策略或运行时间预算
完全相同。普遍融合收益仍未成立；后续独立输入验证协议已冻结为
[`independent_validation_protocol_2026-10-13.json`](independent_validation_protocol_2026-10-13.json)，
包含其余六个完整契约设计，该验证轮尚未执行。
