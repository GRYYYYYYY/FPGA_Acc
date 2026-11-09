# FusionPAR 框架首轮结果（2026-10-13）

C++ 联合状态框架、PR production HBM C-model、VPR 原生检查、timing barrier 和
顺序/交错对照已接通。本文件记录首轮及布局修复阶段的历史结果，彼时证据支持事务正确性，尚无优化收益。
后续分支保留阶段见 [TREE_REUSE_RESULTS.md](TREE_REUSE_RESULTS.md)。

## 验证范围

- C++ 回归包含 67 个检查：完整提交、同 net 多 sink 共享计数、端点变化、旧树释放、
  原子拒绝、过期 placement/timing、重复提交、外来事务、malformed backend、定点范围
  与版本上界、swap/macro/fixed 约束、有界 repair 及局部拥塞后的全网 repair。
- 真实开发设计为 ex5p：150 instances、1,916 connections、678 nets、27,436 RR nodes。
- 四种 QoR 保护模式和一种协议测试模式，每种重复五次，共 25 次运行。
- 逐模式最终完整状态 SHA-256、事件语义和 timing barrier 轨迹可复现。
- cold/shared 顺序模式的最终状态和事件一致。
- 独立审计重新构造 15 次协议提交、40 次拒绝和 40 次 timing barrier，逐对象核对版本、
  owner/occupancy、native certificate 与最终完整序列化状态。

原始实验位于 `work/ex5p_framework_validation_v1/`，包含构建日志、28 个实现文件副本、
输入 manifest、2,197 个原始归档文件的 SHA-256 索引、candidate `.place/.route`、
两套 VPR 工具日志、timing CSV、事件和最终状态。独立结果见
[`ex5p_publication_audit_2026-10-13.json`](ex5p_publication_audit_2026-10-13.json)。

## 受 QoR 保护的开发比较

接受条件固定为 native `(wirelength, CPD)` 严格字典序改善，同时 CPD/WL 不超过初始
合法状态的 102%。以下时间为五次独立 host subprocess 的 wall time 中位数，包含
初始化、候选生成、资源复制、搜索、失败候选、序列化、原生验证和 timing export。
公共输入转换另外耗时约 2.179 s，在机器可读结果的 charged wall time 中等额计入每种模式。
构建成本单独归档。

| 模式 | 每次提交/拒绝 | Host wall time 中位数 | 最终 WL | 最终 CPD (ns) |
|---|---:|---:|---:|---:|
| sequential | 0 / 1 | 8.764 s | 9857 | 5.88580 |
| sequential_shared | 0 / 1 | 8.705 s | 9857 | 5.88580 |
| interleaved | 0 / 3 | 15.532 s | 9857 | 5.88580 |
| interleaved_repair | 0 / 3 | 15.845 s | 9857 | 5.88580 |

这些模式全部保留了初始合法状态。当前条件下交错模式额外支付了逐候选验证成本，
没有得到任何被接受的改进。不能根据 cold/shared 的微小计时差宣称稳定收益；也不能
把两种模式不同的候选/事务次数当作等量 kernel 工作的速度比较。

## 成功提交的协议测试

`protocol_probe` 只检查原生合法性，用于验证真实成功发布和提交后的 timing 消费。
每次运行提交 3 个 move，结束于 timing epoch 4。五次完全一致，最终 WL=9844、
CPD=6.52996 ns；CPD 已超出研究模式的 2% 门槛，因此这 15 次提交仅作为协议证据。

原生 timing exporter 返回全部 1,916 条连接，零未映射项；CPD 与独立原生 STA
在 1 ps 范围内一致。导出采用已加载的完整 RC route tree，不用 PR 的加性 edge
delay 覆盖真实 timing。独立审计确认输出 criticalities 被真实写入每次 barrier。

## 下一阶段

1. 根据下述归因结果研究保留未改变端点的分支。现有 PR 顶层 API 没有初始 route-tree
   参数，需要显式的树复用接口/控制器，不能仅保留 resource occupancy 就假定树已复用。
2. 增加同搜索预算的额外候选/盲修复对照，再判断失败反馈是否有独立价值；保持当前
   QoR 门槛，保留所有失败和成本。
3. 将全量私有副本与全量原生验证成本明确分解，再研究局部状态更新和复用。
4. 加入最佳 placer + PR 强基线和独立验证集合后，才判断是否存在第五篇的独立净益。

上述均为 CPU/C-model/native VPR 结果。RC 处于 bypass，DR 未接入，没有物理 U280
运行；早期 HLS kernel 的改动本轮只做了普通 C++ 回归。

## 失败归因与布局修复增量

归因工具重新读取冻结的 ex5p 候选、逐连接原生 delay 和 RR channel 长度，按 net
去重后的 wirelength 与 VPR 输出一致。三个原始候选的 HPWL 均下降，但真实布线
和时序均退化：

| 候选 | HPWL delta | Native WL delta | CPD delta (ns) | 端点不变但路径变化的连接 | 其中 delay 增加 |
|---|---:|---:|---:|---:|---:|
| 1 | -44 | +22 | +0.20218 | 296 | 214 |
| 2 | -37 | +70 | +0.57813 | 346 | 263 |
| 3 | -32 | +41 | +0.27839 | 315 | 218 |

证据见 [`ex5p_rejection_attribution_2026-10-13.json`](ex5p_rejection_attribution_2026-10-13.json)。
这说明整 net 重路由扰动了大量未移动端点的路径，值得研究分支保留；它不证明
保留分支一定改善时序，完整 RC 树的负载仍可能变化。

新增 C++ `FailureFeedback` 和 `propose_repairs`，由真实失败连接选择相关已移动
实例，在原移动半径内生成最多两个替代合法 move/swap。QoR 拒绝使用原生 delay
反馈；路由失败使用未完成/拥塞连接。原接受门槛不变。79 项 C++ 检查全部通过，
包含从无法路由的位置修复到可路由位置并提交的 fixture。

ex5p pilot 的五种受保护模式均无提交。布局修复模式进行了 3 次 primary 和
3 次额外 repair，六次均被 QoR 门槛拒绝，保留 WL=9857、CPD=5.88580 ns。
该模式单次 host subprocess 为 27.961 s（普通 interleaved 为 15.548 s）；这只是
一次开发诊断，不构成稳定性能比较。各模式候选预算不同，不能据此比较 kernel
速度。独立审计核对了反馈排序、父候选、修复半径/次数、原生 delay 数据桥和完整
状态历史，结果见 [`ex5p_placement_repair_audit_2026-10-13.json`](ex5p_placement_repair_audit_2026-10-13.json)。
原始文件位于 `work/ex5p_placement_repair_pilot_v1/`；单次运行不声称重复性。

alu4/misex3 开发验证固定采用同一策略和每模式两次重复，协议见
[`placement_repair_protocol_2026-10-13.json`](placement_repair_protocol_2026-10-13.json)。
两设计均完成五种模式 × 两次重复，完整状态、事件语义和 timing 轨迹一致；
cold/shared 对照等价。三套新实验使用完全相同的 31 个源文件 SHA-256。

| 设计 | 新运行数 | 额外布局修复总数 | QoR 提交 | 最终 WL / CPD (ns) | interleaved / placement-repair host 秒数 |
|---|---:|---:|---:|---:|---:|
| ex5p | 5（单次 pilot） | 3 | 0 | 9857 / 5.88580 | 15.548 / 27.961 |
| alu4 | 10（两次重复） | 8 | 0 | 9580 / 5.96812 | 24.188 / 51.023 |
| misex3 | 10（两次重复） | 10 | 0 | 10323 / 5.08031 | 20.927 / 46.157 |

alu4/misex3 时间为两次 host subprocess 的中位数，仅作开发成本描述。公共输入
转换另外等额计入机器可读 `median_charged_wall_s`。全部新实验共 76 次拒绝、
25 次 timing barrier、21 次额外布局修复，独立审计通过。15 个 primary 的原生
delay 反馈排序也经独立重算。真实修复触发均为 QoR 拒绝，拥塞触发仍只有单元
fixture 证据。增加修复使时间明显增长，没有改善最终解；不能据此声称收益。

汇总及归档 SHA-256 见
[`placement_repair_status_2026-10-13.json`](placement_repair_status_2026-10-13.json)，
独立审计见 [`alu4_placement_repair_audit_2026-10-13.json`](alu4_placement_repair_audit_2026-10-13.json)
和 [`misex3_placement_repair_audit_2026-10-13.json`](misex3_placement_repair_audit_2026-10-13.json)。
三设计均属于开发集合；尚无独立验证集合或最佳 placer + PR 强基线结果。
