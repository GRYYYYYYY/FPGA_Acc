# FusionPAR 分支保留开发验证（2026-10-13）

本阶段在不修改 TP/RC/PR 上游工程的前提下，实现显式分支保留。ex5p pilot 首次
产生通过原生合法性及原 QoR 门槛的提交；尚不是独立验证集合或论文收益结论。

## 实现与对照

`Engine::prepare(..., reroute_all, retain_branches)` 在 affected net 中按 RR source/sink
是否同时保持不变，选出完整旧分支。`retained_cmodel_router` 维护这些固定分支及
新搜索产生的动态分支，仍调用原有 PR HBM C-model 搜索/提交内核。资源按 net
集合计数，支持 capacity > 1；每次拥塞重试只释放可变部分，保留树仍然占用资源。
搜索失败不隐式退回整 net 重建，整个事务保持原子拒绝。

保留分支的路径、端点和 route version 必须与旧状态完全一致。FP 再独立检查完整
树、路径和容量；原生 VPR 重新验证合法性和 RC 时序。资源版本仍保守地覆盖整个
affected-net 的旧/新节点并集，本阶段没有声称减少并发冲突范围或 HBM 流量。

两种模式使用同一 FP 控制器、原 task priority/id 排序和单 task issue width：

- `interleaved_tree_control`：空树开始，全量重建受影响 net。
- `interleaved_tree_reuse`：载入不变端点的分支，只搜索剩余连接。

额外保留原 `interleaved` 作为 PR 控制器等价检查。runner 要求新空树对照与原 PR
事件语义、搜索数、expanded 数和候选状态摘要完全相同，否则该套实验失败。
接受条件依旧是 native `(WL, CPD)` 严格字典序改善，且两者不超过初始值的 102%。

97 项 C++ 检查通过。新增覆盖了保留路径/version、多 net 共享 capacity=2、端点
变化、失败重试回退、损坏后端、互斥选项，以及与原 PR 的拥塞协商/搜索量对照。

## ex5p pilot

`work/ex5p_tree_reuse_pilot_v2/` 包含六种模式各一次、每种三个 primary attempts。
分支保留模式 1 次提交、2 次 QoR 拒绝；其他模式没有提交。首个提交保留 324 条
连接，原生 WL 从 9857 降到 9849，CPD 从 5.88580 ns 降到 5.83751 ns。
后续 timing barrier 消费了提交后的完整原生 criticality 数组。

| 模式 | 最终 WL | 最终 CPD (ns) | 路由整体计时 (s) | Host subprocess (s) |
|---|---:|---:|---:|---:|
| 原 interleaved | 9857 | 5.88580 | 4.223 | 16.044 |
| 空树 control | 9857 | 5.88580 | 3.183 | 14.819 |
| tree reuse | 9849 | 5.83751 | 0.811 | 12.911 |

这是单次 pilot，不报告稳定 speedup。后续两个候选是在已改善状态上重新生成，
不能将它们逐候选直接配对为相同工作。所有失败和原生检查均计入 host 时间；
输入转换另行等额计入 charged time。独立审计通过，见
[`ex5p_tree_reuse_pilot_audit_2026-10-13.json`](ex5p_tree_reuse_pilot_audit_2026-10-13.json)。

`work/ex5p_tree_reuse_pilot_v1/` 是一次 architecture 路径输入笔误导致的 prepare
失败记录，未启动候选运行，保留用于追踪；正式 pilot 使用上述 v2。

## 复验与证据边界

固定策略见 [`tree_reuse_protocol_2026-10-13.json`](tree_reuse_protocol_2026-10-13.json)。
第一版 ex5p、alu4、misex3 各六种模式 × 两次重复已完成，独立审计均通过。ex5p
每次有 1 个提交，alu4 每次有 1 个提交，misex3 无提交；空树对照均复现原 PR。
ex5p 分支保留的两次 host 时间分别为 36.715 s 和 14.688 s，第一轮更慢，原始
记录显示 native 检查和路由计时都有波动，未删除该样本，不据此宣称稳定加速。

alu4 成功提交后的第三个候选涉及移动 I/O，暴露了本地 route 导出的格式错误。
VPR `read_route.cpp` 对 I/O 要求 `Pad: <ptc> Switch:`，不能带逻辑 pb-pin 名称；
原 PR 固定端点 serializer 遇到新 I/O 节点时会附加从 RR 图读取的 pin 名称。
原生门槛阻止了该候选发布，原始失败保留在 v1 实验中。

本地适配器现从原生基线的 `Pad` 描述学习实际 I/O physical type，对这些类型的
节点显式输出不带 pin 名称的 Pad 格式，不用边界位置或硬编码类型名判断 I/O。
同一候选状态（SHA-256 完全一致）在修复后通过原生检查，WL=9548、CPD=5.96812 ns；
VPR、器件、网表、placement 和 RR graph 的输入 SHA 均未改变。证据见
[`io_pad_regression_2026-10-13.json`](io_pad_regression_2026-10-13.json)。

修复后的三设计复验按
[`tree_reuse_io_fix_protocol_2026-10-13.json`](tree_reuse_io_fix_protocol_2026-10-13.json)
执行，每种模式两次重复，聚焦原 PR、空树和分支保留三个模式；C++ 算法和门槛
不变。完整 v1 的六模式结果单独保留，不能合并为相同版本的性能样本。
三个设计都属于开发集合，尚没有独立验证集合结果。

## 修复后的开发复验（v2）

三设计 × 三模式 × 两次重复，共 18 次运行，均完成独立审计。完整状态 SHA、
事件语义和 timing barrier 轨迹在重复间一致；三设计的空树控制器均与原 PR 事件
和搜索量相同。共 6 次 QoR 提交、48 次拒绝、24 次 timing barrier，没有非法发布。
各设计两次最终结果相同：

| 设计 | 每次 reuse 提交/拒绝 | 初始 WL → 最终 WL | 初始 CPD → 最终 CPD (ns) | 空树 host 秒数（两次） | reuse host 秒数（两次） |
|---|---:|---:|---:|---:|---:|
| ex5p | 1 / 2 | 9857 → 9849 | 5.88580 → 5.83751 | 15.371 / 16.583 | 13.016 / 13.478 |
| alu4 | 2 / 1 | 9580 → 9548 | 5.96812 → 5.96812 | 23.465 / 23.507 | 15.089 / 14.926 |
| misex3 | 0 / 3 | 10323 → 10323 | 5.08031 → 5.08031 | 19.852 / 20.880 | 14.016 / 13.763 |

空树和原 PR 都没有接受提交。ex5p 的 WL 改善约 0.0812%、CPD 改善约 0.8204%；
alu4 的 WL 改善约 0.3340%，CPD 不变。公共转换成本在机器可读 charged time 中
对每组等额加入。这里只报告开发时间样本，不把两次重复或较快的一版样本当成稳定
加速结论；v1 的慢样本继续保留。

同一旧状态、同一布局 move 的首个候选中，ex5p 的 kernel 搜索次数从 900 降到
455（保留 324 条连接）；alu4 从 1801 降到 47（保留 1068 条连接）。这些次数包含
拥塞迭代。两设计在首次提交后候选序列发生分歧，因此只把相同完整旧状态和 move
的事件列为逐候选对照。misex3 三个候选均可配对，搜索量均下降，但 QoR 没有达到
接受门槛，说明减少搜索并不保证改善最终解。

机器可读汇总与全部 SHA 绑定见
[`tree_reuse_status_2026-10-13.json`](tree_reuse_status_2026-10-13.json)。原始归档为
`work/{ex5p,alu4,misex3}_tree_reuse_development_v2/`。独立结果见
[`ex5p_tree_reuse_v2_audit_2026-10-13.json`](ex5p_tree_reuse_v2_audit_2026-10-13.json)、
[`alu4_tree_reuse_v2_audit_2026-10-13.json`](alu4_tree_reuse_v2_audit_2026-10-13.json)、
[`misex3_tree_reuse_v2_audit_2026-10-13.json`](misex3_tree_reuse_v2_audit_2026-10-13.json)。

路径保留不等于 delay 保留：共享 RC 树的分支负载可能改变。每个候选仍以完整
原生时序为准。分支复用本身也是已有路由技术，不能直接当成 FusionPAR 独立贡献；
首先要让分阶段 batch 控制也使用同一 retained-tree 路由器，隔离普通树复用与
交错调度的贡献。仍需最佳 placer + PR 强基线、匹配搜索预算的反馈对照和完整
开销分析。已定位的 TilePlace 冻结输入及其不可直接比较的预算/目标差异记录在
[`strong_baseline_inventory_2026-10-13.json`](strong_baseline_inventory_2026-10-13.json)，
尚未把这些历史结果当成已执行的 TP + PR 强基线。

此处没有物理 FPGA 运行。`copy_payload_bytes` 只计 Engine 显式复制的逻辑 payload，
不包含 PR 或新树控制器内部全部 scratch 分配，不能解释为硬件流量。
