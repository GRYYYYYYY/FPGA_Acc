# 未通过门槛与下一阶段准入

基准 `b32afa4303a5574dde7171b4ae6e3d07aeb8a06c`；只读审计日期2026-11-10。
当前结论：主候选A、备选E，均未达到完整论文投稿门槛。阶段一不发起新实验。

## A主候选的阻断项

| 门槛 | 当前事实 | 最小补证/验收条件 | 不允许的替代 |
|---|---|---|---|
| A1 单一方法贡献 | native-feedback/rollback已有实现；frontier消融CPD净收益0 | 提出一个源码中可定位、与已有工作区分、可关掉的机制；证明正确性和适用条件 | 把框架规模、普通事务或VPR调用当贡献 |
| A2 来源闭环 | 新13例统一generic指纹；历史V4 parser不一致 | 选择一个CPU源清单，绑定输入、parser、VPR、adapter、runner、binary与配置；历史版本单列 | 将旧六例−5.049%拼入当前主表 |
| A3 完整分母 | 9/13完成；四例输入失败 | 展示全部13例和失败阶段；如修复，另开注册cohort保留旧结果 | 删失败、换design、把覆盖率说成100% |
| A4 强公平baseline | 同netlist SA/AP可运行；AP不足以代表最强timing placer | 可执行SA continuation/restart与同TP无新增机制；同问题/目标；分别给等wall与等closure结果 | 等closure视为等wall；取较弱AP唯一对照 |
| A5 完整成本 | 有单例generic/prefix测量；大案例oracle很贵 | 完整run计时，包含拒绝、转换、反馈、serialization、validation、重建；嵌套timer不重复相加 | HLS latency、proposal/kernel计时、排除失败的速度 |
| A6 机制消融 | prefix一个开发例1.285×；suppression无CPD改善 | 同源只切一个开关；保持轨迹或按预注册QoR比较；同时报告构建/失效成本 | 换source/parser/目标得到的数字当消融 |
| A7 新设计 | 现有9例已有历史暴露 | 预先冻结有来源与暴露记录的独立设计；固定参数、不看标签调参；失败计入 | 重跑旧heldout后改名strict unseen |
| A8 统计与稿件 | deterministic repeats不是独立design；IEEE工作稿未最终审计 | 受控配对运行、完整样本、明确作用范围；6+1页每图都有claim/evidence映射 | shared-host单次结果宣称普遍加速 |

第二阶段只整理现成小型证据，优先顺序：A2/A3→A4已有baseline清单→A5计时账本→A1/A6可检验机制→A7新设计准入。
源指纹或成本不成立时，先修正研究假设；不通过大量追加运行规避判断。
后续新实验必须有不可变协议文件及其提交SHA，明确案例、seed、二进制、参数、资源/墙钟预算、超时、重试规则、统计口径和接受阈值。
本表不是执行协议；没有授权脚本在读取本表后自动启动作业。

## 其它方向不能带入主稿的开放项

| 工程 | 门槛 | 当前判定 |
|---|---|---|
| PersistRoute | 最终tree-seed同版本功能验证 | 180MHz实现清单明确未重跑hw_emu；早期RTL记录不可继承 |
| PersistRoute | 反例修复闭环 | 未找到用户所指反例→修复→最终版本终态的完整绑定；现有test源码不等于已验收最终硬件 |
| PersistRoute | 统一QoR | corrected矩阵混用spmv weight128；6例合法、Balanced仅3/6，WL几何平均+5.4655% |
| PersistRoute | 驻留性能 | 有BO常驻与Resource差分；seen/closed每launch清零；缺收益消融及板卡完整成本 |
| TilePlace硬件 | 同一候选完整功能+物理采纳 | October 4功能过；后续best physical仍−0.047ns/224失败；未采纳 |
| RouteCast | 原full9预测、unseen、净收益 | 未验收、strict unseen=0；不能由容量可行或路径等价替代 |
| RouteCast联合容量 | 止损 | 2026-10-24截止已过；10月21评审无获准推广候选；不继续同信息变体 |
| E备选 | 精确前提和完整成本 | 单个ABBA只搜索；需nonnegative、NET/source、失效、incomplete语义验证，以及优化baseline与实际消费者净收益 |
| FusionPAR | 等最终QoR+等总预算优于TP/分阶段/消融 | 现有负结果不满足；TP→PR 0/15质量合格，九预算FP仅1/3设计胜TP |
| FusionPAR | 支持与影响范围 | 4/6独立输入；全revision/affected-net并集；没有最小冲突域并发证明 |
| 所有工程 | 板卡速度、能耗、带宽 | 没有实测证据；硬件实现/仿真/周期模型不得代替 |

## DieRoute v292正式门槛（全部保留）

| ID | 原正式要求（摘要） | v292状态 |
|---|---|---|
| G1 | 输入、baseline源码/命令冻结，真实layer/SLR元数据，graph/route往返 | in_progress |
| G2 | C++完整路由闭环、精确占用/共享、corridor释放修复、确定性事务及五重复哈希 | in_progress |
| G3 | 可信multi-die workload及拓扑/容量缩放，不以microbenchmark替代 | in_progress |
| G4 | native合法、失败不增，SLL/CPD/WL不劣于冻结强baseline | in_progress |
| G5 | reservation/mapping/shadow/migration/topology五类消融 | in_progress |
| G6 | csim/csynth/cosim、真实HBM接口/connectivity、U280时序与资源 | in_progress |
| G7 | 物理板端到端≥3×目标、能耗、重复及统计 | pending_external_hardware |
| G8 | 论文、claim matrix、可复现artifact及逐门槛终验 | in_progress |

v292矩阵SHA：`bf266cd9b47a57fc2ab87a700e638c28e01e66558d6d4665f574d2042085f527`。
最新11月7日handoff继续限制运行。11月10日原五个PID不存在、builder无终态；记录事实，不启动任务、不改变资源。
不能从448项局部claim数量推断G1–G8已过，也不能把历史running字段当进程存活证据。

## 紧凑证据包仍需补齐的范围

本阶段`PHASE1_CHECKS.json`是检查账本，`PHASE1_CASES.csv`仅为TP13例索引；它们不是阶段二要求的完整`evidence/`包或跨项目all_cases。
第二阶段须为选定主张复制必要小型原件并附：source commit与实现指纹（不能将二者混写）、design/config/seed、输入/工具/binary/result SHA、真实命令、exit/失败/超时、逐例legality/WL/CPD/完整时间。
历史记录没有源码commit或终态时填`unknown`及原因，不用本次审计commit补作历史source commit。
大文件仅登记原路径、当前大小、已有SHA与是否本次重算；迁移路径和原路径均保留。18处延期引用不是18个不同大文件，须去重后登记。
优先需要：TP13全案与404trial索引、old-parser负记录、单源消融和CPU timing；October 4与失败4ns只作独立hardware gate；PR版本差距、FP负结果和RC复用作为选择证据保留。
未来`all_cases.csv`、`timing_breakdown.csv`、`hardware_gate.csv`、`missing_evidence.csv`必须从原件生成且不覆盖本阶段账本。

## 第一阶段验收边界

本阶段结束后先交付审计与选题。当前不触发阶段四大规模计算；完整投稿决定仍为NO-GO。
在后续证据整理发现不可修复的来源缺口、机制无独立新颖性或公平baseline无净收益时，应尽早不投稿，保留最小后续补证方案；不得转用放宽QoR、事后更换案例或无卡加速叙述。
