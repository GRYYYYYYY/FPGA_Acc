# FusionPAR 先行框架验收

本次工作落实“TP/RC 尚在探索时，先搭建可以接入上游能力的 FP 框架”：统一状态、
move–route 原子事务、真实 PR 闭环、失败反馈与有界修复，以及可复现的对照实验。
验收以现有 [G1–G3 计划](framework_plan.json) 和
[接口契约](FRAMEWORK_CONTRACT.md) 为依据。总体系结构文档中的完整 FPGA 数据面、
HBM 二进制接口和论文性能主张是后续目标，不以本 CPU 框架的验收替代。

当前实现和测量支持范围内的先行框架已经完成。独立输入支持为 **4/6**；两个根
时钟输入仍不受支持。现有策略没有证明普遍融合收益，不能据此宣称论文整体完成。

## 逐项检查

| 要求 | 当前实现与直接证据 | 判定及范围 |
|---|---|---|
| 不等待高级 TP/RC 即可运行 | [接口](../include/joint_state.hpp)中的 Proposal、Router、Sketch、Validator、Acceptance；host 使用确定性合法 move/swap，Sketch 关闭；CMake 编译既有 PR production C-model | 完成软件接入边界；尚无动态 placer 插件，也未验证 RC 预测效果 |
| 统一布局、路由、资源、时序状态 | State 保存 placement/site/route/resource 版本、完整路径、criticalities 和 epoch；[联合状态实现](../src/joint_state.cpp)负责验证及发布 | 完成 CPU 内存契约；不是 64-byte 外存 ABI |
| 原子提交，失败不改可信状态 | prepare 使用私有候选；commit 验证事务归属、消费状态、完整 revision 和 timing epoch 后统一发布；[C++ 回归](../tb/joint_state_tb.cpp)注入路由、原生检查、QoR、版本与损坏路径失败 | G1 完成；单线程、整个 revision 保守失效，不声称并发不相交提交 |
| 移动后的端点与占用正确 | 重映射受影响 net 全部端点，释放其旧占用；从完整路径按 net 重算共享所有权；提交时涉及资源版本恰增一 | G1 完成；source-excluded PR 路径约定及共享分支语义见接口契约 |
| 合法 move/swap 与限制 | 显式 allowed_sites、fixed、type、macro、site 唯一性检查；原生适配器再检查布局契约及 VPR 合法性 | 完成声明输入边界内的约束；不支持的映射和根时钟拒绝转换 |
| 时序屏障与过期拒绝 | host 在初始状态及每次成功提交后提交绑定当前 revision 的完整原生 criticality 数组；独立审计重建 timing 轨迹 | G1/G2 完成；单次搜索内使用固定快照 |
| 真实设计最小闭环 | [转换器](../tools/prepare_vpr_bundle.py)、[host](../host/joint_host.cpp)、[原生验证器](../tools/validate_candidate.py)；支持设计实际移动、PR 路由、VPR/STA、提交和后续 timing barrier 均留档 | G2 完成；入口为已有合法 routed design，不包含从 packing 启动的完整 P&R |
| 路由分支复用 | [retained_router.cpp](../src/retained_router.cpp)在私有工作区重建保留树，核对未变端点及完整分支；空树对照与 PR 搜索语义一致；多 owner 回归覆盖共享占用 | 完成；真实开发和独立验证均包含保留分支审计 |
| 失败反馈、有界修复、终止 | [joint_repair.cpp](../src/joint_repair.cpp)消费失败连接或原生 delay/WL 证据，修复相关移动实例；host 实施半径、去重和每次最多两个 repair；九评估模式将 primary/repair 计入同一预算 | 完成机制；现有反馈模式仅作实验，不推荐为普遍更优策略 |
| 重复性与独立状态审计 | 113 项 C++ 检查、6 个缓存测试；[独立审计器](../tools/audit_development.py)重建完整状态、版本、时序、原生绑定和接受门槛 | CTest 3/3；12 组均构建测试通过，8 组完成 host 的五次状态/事件/时序重复及独立审计 |
| 同组件、共享状态、交错及修复对照 | [控制器对照](CONTROLLER_BASELINES.md)、[等预算对照](FEEDBACK_BUDGET_RESULTS.md)、[独立结果](INDEPENDENT_VALIDATION_RESULTS.md) | G3 完成比较；分阶段 batch 与逐次交错的实际评估次数不同，另列九次等评估比较 |
| 较强的 TP 参考 | [TP 参考报告](TP_CHECKPOINT_REFERENCE.md)对所有已访问合法候选使用共同最终目标，包括 TP 自身拒绝的候选；另有 15 次九闭合调用、135 个候选原生检查 | 已完成强参考；在线目标、候选工作量和 CPU affinity 不同，不能报告配对加速比 |
| 完整费用与失败分母 | 完整 host subprocess 时间包含候选生成、失败、修复、验证和反馈；每个样本加一次完整转换费用；构建测试另列；native/router 不重叠分解；根时钟失败保留费用及日志 | G3 完成口径；没有将阶段时间、复制字节或 CPU 计时解释为 FPGA 性能 |
| 冻结独立验证与可追溯证据 | [预登记协议](independent_validation_protocol_2026-10-13.json)、源码/输入冻结、原始 study、[逐样本结果](independent_validation_status_2026-10-13.json)、[最终证据复核](framework_evidence_recheck_2026-10-13.json) | 12 组全部尝试，8 组审计通过，4 组转换失败；策略未按结果调参，也未替换失败设计 |

## 完成证据与研究结论

最终复核工具为 [recheck_framework_evidence.py](../tools/recheck_framework_evidence.py)。
它重新生成汇总并与保存结果比较，核验当前冻结源码、归档源码和输入哈希，检查
12 组构建/测试/转换日志，再核验八份发布审计所依赖的归档文件、host 二进制、
评估预算及完整转换计费。它不会重跑或覆盖已测量的 native P&R，也不生成新的
性能样本。原审计器的检查范围已经结合实现和回归逐项阅读；证据复核检查这些
审计所依据的字节仍然相同，不能把复核误称为独立实现的第二套 P&R。

独立验证有 80 次 host 运行、440 次候选评估、35 次受 QoR 门槛保护的提交、
405 次拒绝、115 次时序屏障、105 次布局修复。所有支持设计的两个九预算模式
都实际评估九次。三个 primary 的分阶段/交错对照均保持初始质量；九预算反馈
在三个设计上最终线长更差，一个持平。这支持框架可执行、可验证的结论，
不支持“交错/反馈普遍更优”。TP 开发集强参考也给出混合结果。

原 `framework_status_2026-10-13.json` 是首轮 25 次运行的历史检查点，其中的
remaining 和源码哈希属于那个阶段；保留其字节。当前完成状态从
[manifest](manifest.json)、[计划](framework_plan.json)与本验收说明进入。
预登记协议的 `preregistered_not_run` 字段同样保留原始字节，运行终态由 study
和结果记录表达。执行成功不等于所有输入支持，`all_suites_passed` 保持 false。

## 后续研究与明确未实现项

- **输入覆盖：** 根时钟及其他 ignored-net 的成员身份、坐标、pin class 和回写
  完整性仍需实现，见 [GLOBAL_NET_SUPPORT_NOTES.md](GLOBAL_NET_SUPPORT_NOTES.md)。
  不得删除这些网络来使失败设计通过。
- **上游策略：** 接入高级 TP 候选策略和 RC 预测器，分别做消融；DR 保持可选。
  当前简单候选生成器会全量枚举、检查和排序，尚未解决其规模效率。
- **研究收益：** 依据失败归因改进策略后重新开发和冻结验证；本次集合已被观察，
  不能继续将其当作改进策略的未接触验证集。正收益尚待证明，不能作为已有结论。
- **完整流程和硬件：** 从 packing 开始的全流程、并发联合提交、二进制/HBM ABI、
  事务池与 PE 设计、完整 HLS/RTL 闭环及物理 U280 实测均未完成。早期资源增量
  kernel 不能代替联合事务硬件。没有板上吞吐、带宽、能耗或加速比结果。

这些边界已经存在于先行框架计划和实验协议中；此次验收没有将其标成完成。
