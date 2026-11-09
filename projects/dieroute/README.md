# DieRoute 独立工程

目标是多 die/SLR 分层路由：SLL corridor 预留、单 owner 边界状态与 shadow
同步、HBM 分区和任务迁移。完整验收范围见
[`experiments/research_plan.json`](experiments/research_plan.json)，研究尚未完成。

## 截至 2026-10-20 的验证结果

apex2 seed6 的独立后验联合交换与线长清理已联合达标：WL 19306→19228，
CPD 11.1843→11.1417 ns，模型跨层转移 1505→1199，原生合法且无容量超限。
此前 7 个交换方案与后续 3 个方案均未联合通过；从时序通过但线长超限的候选出发，
最多检查 8 个线长超额网络的清理在首个网络接受后达到停止条件。
最终路由经新旧 VPR 重新加载，指标和 3500 条连接时序 CSV 一致。
见[最终复核](work/posterior_seed6_final_joint_pass_native_recheck_20261020/compatibility_audit.json)
和[结论矩阵 v18](work/current_research_claim_matrix_v18_20261020/matrix.json)。
这是单独的事后开发结果，不能替换仍在运行的冻结 seed6–10 完整流程结果，
也不证明统计泛化、完整流程重复性或 FPGA 加速。

扩大规模的 12 组后验父路由实验已全部完成独立复核：12/12 原生合法，
线长与模型跨层转移数全部下降，但仅 11/12 通过三项联合不退化检查。
最后一组 elliptic/28×22/cw320 的线长下降 22.65%，模型跨层转移数
1983→1893，CPD 却上升 0.0384% 至 10.4245 ns，必须保留为质量退化。
见[完整十二组审计汇总](work/width_coverage_all_twelve_summary_20261020/audit.json)。
这些是三个电路、两种规模、两种通道宽度的单种子后验观察，不替代原保留集，
不证明全配置质量不退化、统计泛化、物理 SLL 改善或 FPGA 加速。

独立的后验修复已消除 elliptic/28×22/cw320 的 4 ps 回退：容量感知闭包恢复
2220 个网络，原生合法，WL 43832→42492，CPD 保持 10.4205 ns，模型跨层转移保持 1983。
三次直接恢复尝试均因冲突失败；四次探测的写回与原生验证记录共 427.63 秒，
尚不包含原路由、诊断、闭包构造与审计。原十二组结论仍为 11/12 联合通过。
见[修复审计](work/elliptic_capacity_restore_closure_20261020/independent_native_audit.json)。
进一步的局部交换仅改动 3 个网络即可在 elliptic 退化案例上达到 WL 33918、
CPD 10.4143 ns、模型跨层转移 1895；另外两个 5 网络候选达到 WL 34022、
CPD 10.4073 ns、转移 1908。三个不同候选均原生合法、通过相对原基线的联合质量检查，
五次独立搜索重放候选逐字节一致（仅搜索约 2.37～2.49 秒，未计原生验证或原路由）。
见[局部交换汇总](work/elliptic_local_exchange_20261020/native_summary.json)。
迁移到已知退化的 apex2 seed1 时，自动选点规则找出 464 ps 回退，但原始交换
增加跨层转移；双约束和回退虽产生合法中间改进，仍未达到原基线 CPD 10.8372 ns。
原保留集结果继续保留，不能据单案例成功声称普遍有效。
后续自动刷新与受约束交换将该案例的 CPD 从 11.2084 ns 降至 11.0409 ns，
最新候选 WL 18169、模型跨层转移 1511，原生合法，但仍未达到原基线。
最后一步仅改善打印精度下的 0.3 ps，不构成统计显著性证据。
见[最新私有候选审查](work/apex2_seed1_stage3_current_ceiling_20261020/private_acceptance_review.json)。
后续将阻塞网络优先路由，并使用原生打印 CPD 的整数 ps 上限，避免预算计算
额外收紧 1 ps。经原生验证接受的中间结果进一步达到 CPD 10.9519 ns、WL 18666、
模型跨层转移 1462；仍差于原基线 CPD 10.8372 ns，完整研究验收尚未通过。
见[第二阶段候选审计](work/apex2_seed1_rounded_blocker_first_refinement_20261020/stage_002/exchange/native_queue/task1541_reverse/independent_native_audit.json)。
该轮最终尝试 9 阶段、接受 8 阶段，终态 CPD 10.8721 ns、WL 19285、跨层转移 1408，
仍未达到原基线。第九阶段候选虽降至 10.8635 ns，但 WL 19377 超过原基线 19372，
因此被拒绝；原生接受链、预算取整与执行顺序的独立审计均通过。
见[终态审计](work/apex2_seed1_rounded_blocker_first_refinement_20261020/independent_audit.json)和
[策略审计](work/apex2_seed1_rounded_blocker_first_refinement_20261020/policy_audit.json)。
后续恢复网络 82 的短树，再采用原生通道线长目标，得到原生合法的
CPD 10.8554 ns、WL 19346、跨层转移 1419，距原基线仍差 18.2 ps。
该目标使用 RR 图的 CHANX/CHANY `node_length`，在两条已验证路由上精确重现
VPR 线长；小图路径枚举通过 10240 项检查。后续候选 CPD 10.8500 ns，
但 WL 19379 超基线 7，未接受。仅最少跳数目标的两个候选也均因实际线长超标被拒绝。
见[当前私有改进审查](work/apex2_seed1_postcleanup_wirelength_exchange_20261020/private_acceptance_review.json)、
[实际线长核对](work/apex2_exact_wirelength_weights_20261020/audit.json)和
[逐网计费审计](work/apex2_seed1_exact_wirelength_refinement_20261020/wirelength_audit.json)。
进一步调整目标网络接收端顺序后，apex2 seed1 的后验修复首次联合达标：
原生合法，WL 19372→19170，CPD 10.8372→10.8308 ns，模型跨层转移 1581→1452。
该轮两个不同候选均联合通过，接受较短者；接受链、预算/执行顺序、增量线长与
接收端顺序四项独立审计通过。最终 CPD 裕量仅 6.4 ps，且为已观察案例的多轮
后验研究，不能替换原保留集结果、证明统计泛化或 FPGA 加速。
见[联合通过审计](work/apex2_seed1_reverse_sink_wirelength_refinement_20261020/independent_audit.json)。
新旧 VPR 对最终路由的独立重新加载也已通过：两者均原生合法、WL/CPD 相同，
3500 条连接的取整 ps 时序 CSV 字节一致。见[最终重新加载审计](work/apex2_seed1_final_joint_pass_native_recheck_20261020/compatibility_audit.json)。
将最终冻结策略迁移至已知退化的 seed5，连续接受两阶段后从 11.3248 ns 降至
11.2868 ns，仍未达到 11.2036 ns 基线。第三阶段候选合法、WL 17962→17930，
但 CPD 不变，被原严格 CPD 改善规则拒绝；四项独立审计通过。
见[冻结策略迁移审计](work/apex2_seed5_frozen_reverse_wirelength_refinement_20261020/independent_audit.json)。
另行启动的后验实验允许 CPD 不增加且线长严格下降的中间步骤，以严格字典序
`(CPD, WL, 跨层次数)` 接受候选；原生合法性、容量和原基线最终门槛不变。
该策略变化不计为原冻结迁移成功或独立留出验证。
后续按排名尝试并列最差连接，并改用延迟优先目标，将 seed5 降至 11.2247 ns，
仍未达标。再对当前关键网络做基线容量闭包恢复，三个固定构造去重为一条路由，
原生联合通过：WL 18925→18917，CPD 11.2036→11.2020 ns，模型跨层转移保持 1442。
该修复恢复了 856 个网络中的 789 个，仅保留 8 的线长收益及 1.6 ps 时序裕量；
不能替换原保留集结果、证明统一冻结策略泛化或硬件加速。
见[闭包构造与原生审查](work/apex2_seed5_critical_capacity_closure_v2_20261020/independent_construction_review.json)。
最终路由的新旧 VPR 独立重新加载已通过：原生合法性、WL/CPD 及 3500 条连接的
取整 ps 时序 CSV 均一致。见[最终重新加载审计](work/apex2_seed5_final_joint_pass_native_recheck_20261020/compatibility_audit.json)。

另行冻结了 apex2 seed6～10 的新质量验证队列，算法、参数与失败保留规则在新
基线结果产生前记录。五个原生基线均合法，完整图往返及原生索引代价审计通过，
共检查 1681560 个节点和 2807805 条边。基线和原生质量验证使用源码绑定 VPR，
父路由恢复使用原配置中预先绑定的 FIFO 时序引擎；不支持 FIFO 的首次启动失败
均保留，且发生在 C++ 路由器启动前。逐种子父路由审计及原 sweep/refresh 已排队，
尚无该队列的最终候选质量结论，也不作性能或跨电路泛化结论。
后续两个原生修复模式及固定容量闭包也已接入自动队列，各阶段独立审计后
才允许推进；归档数据回归不计入这五个新种子的质量结果。
见[预先冻结策略](work/prospective_apex2_seeds6_10_baselines_20261020/candidate_policy.json)和
[图与原生代价审计](work/prospective_apex2_seeds6_10_native_costs_20261020/independent_audit.json)。

源码绑定的 VPR 兼容性扩展发现独立限制：原构建的 `MAX_NUM_LAYERS=2`，
在三层输入创建网格时退出，尚未进入路由加载；这不是候选路由非法的证据。
见[失败定位](work/source_bound_route_compatibility_20261020/failure_review.json)。
仅将该上限改为 4 的隔离源码构建已成功，独立审计确认只有该头文件发生预期变化，
时序采样逻辑保持一致，完整构建依赖审计也已通过。兼容性准备脚本引用错误的
构建清单文件名而停止，失败记录已保留；修正后的 v2 已在新目录启动 elliptic、
apex2 基线与候选验证，结果仍待审查，尚不能宣称新旧工具兼容。
见[源码差异审计](work/vpr_source_bound_four_layer_build_20261020/independent_layer_delta_audit.json)。
v2 的 elliptic 和 apex2 比较及汇总审计均已通过：基线与候选各自的 6270、
3500 条连接，新旧工具的原生合法性、线长、CPD 及取整到 ps 的时序 CSV 字节均一致。
该结果仅覆盖四条冻结路由，不证明全部输入兼容或历史二进制的源码身份。
见[四路由兼容性汇总审计](work/vpr_four_layer_compatibility_closure_v2_queue_20261020/closure_audit.json)。

通用闭包实现通过 62500 组小规模穷举检查；另一批固定选网规则的三个电路压力验证
均原生合法且联合不退化，但仅保留较小线长收益，不证明普遍修复、统计泛化或硬件加速。
见[三电路审计](work/capacity_closure_crosscase_20261020/independent_audit.json)。

ripup predecessor helper 候选已完成物理链接和独立检查：604605 条网络全部布通，
但保留 300 MHz 约束下 WNS −1.556 ns、TNS −13202.495 ns，35905 个 setup 失败端点。
相对串行发布父版 WNS 改善 0.611 ns，失败端点减少 13826 个，仍未达到时序目标，未采纳。
见[最终同口径比较](work/ripup_predecessor_final_timing_comparison_20261020/audit.json)。
有效 DRC 严重级别和外部 IO 延迟例外仍保留，不能据此声称默认 DRC、降频签核或实卡性能通过。
协商扫描 helper 已完成物理实现与独立审计：611332 条网络全部布通，
300 MHz 下 WNS −1.236 ns、TNS −12223.346 ns，36299 个 setup 失败端点。
相对 ripup predecessor 父版 WNS 改善 0.320 ns，但失败端点增加 394 个，仍未采纳。
见[最终路由审计](work/negotiate_scan_helper_routed_review_20261020/independent_audit.json)。
后续 insert lookup 边界候选通过 75 次 RTL 调用，总周期 324190→324260（+0.0216%）。
调用方 RTL 在验证 helper 前寄存 lookup 结果；实际 XO 编译及接口审查已通过，
完整物理链接正在运行。物理综合是否保留边界及最终时序收益仍待验证。
见[实际 XO 审查](work/insert_lookup_boundary_hw_20261020/compiled_XO_review.json)。

新的 scratch 独立 AXI bundle 候选通过 75 次 C 差分及 75 次 Verilog 调用，
实际 XO 确认仅新增预期 scratch 接口，29 个参数及寄存器偏移保持一致。
同一测试平台总周期 315265 → 314460（−0.255%），HLS LUT/FF 增加
5643/4465，估计周期仍为 2.433 ns。完整物理链接已成功；独立归档检查点审查确认 597754 条网络全部布通，
但 300 MHz 建立时序失败：WNS −1.536 ns、TNS −11852.657 ns、31705 个
失败端点。保持、脉宽、总线偏斜数值检查及无严重 DRC 检查通过，仍保留
329 条 Warning、5 条 Advisory 和外部 IO 延迟缺项。工具自动将内核降至
205.3 MHz、HBM 降至 396.1 MHz，降频后的完整签核和板上吞吐仍未证明。
该候选尚未采纳。见[独立物理审查](work/scratch_split_routed_review_20261018/independent_audit.json)。
见[RTL 审查](work/scratch_split_bundle_RTL_20261018/independent_audit.json)和
[实际 XO 审查](work/scratch_split_bundle_hw_20261018/compiled_XO_review.json)。

traffic 读缓冲候选已完成硬件 link，并完成独立归档检查点报告审计：
585455 条网络全部布通、路由错误为零；hold 与脉宽通过，DRC 无 Error 或
Critical，保留 330 条 Warning 和 5 条 Advisory。原定 setup 验收失败：
WNS −1.951 ns、TNS −29360.275 ns、56894 个失败端点。镜像时钟拓扑
DATA_CLK 为 189 MHz、HBM 为 412 MHz；拓扑名称本身不证明最终 CU 时钟关联，
也未证明降频后的完整时序或板卡运行。该候选未被采纳。
见[硬件独立审计](work/traffic_read_buffer_routed_review_20261017/independent_audit.json)。

与上一轮相比，WNS 改善 0.353 ns，但 TNS 恶化 1655.742 ns、失败端点增加
4608 个，不能判为整体优化成功。最差数据路径在 SLR0 内，扇出 19，
5.132 ns 数据延迟中布线占 98.461%；该单路径诊断不能解释所有失败端点。
见[同口径比较](work/traffic_buffer_vs_lean_requested_clock_comparison_20261018/audit.json)
和[最差路径定位](work/traffic_buffer_worst_data_net_locality_20261018/audit.json)。
研究仍未完成，原定验收目标保持不变。

## 2026-10-17 研究结论

2026-10-16：冻结的通用关键路径刷新修复已完成三设计原生验证和独立审计，
三例均达到线长/CPD/跨层联合基线：ex5p 为 11397 / 10.4526 ns / 991，
diffeq 为 11206 / 7.74031 ns / 727，alu4 为 9424 / 10.3951 ns / 886。
该阶段从已审计 v2 终态开始，自动为 ex5p 接受 3 次整网更新；另两例原已达标，
本阶段未修改。选择规则不含指定网号；每次更新要求完整原生 CPD 严格下降，
允许使用全局线长余量，并串行刷新 STA/容量。ex5p 时序裕量仅 0.5 ps。
同配置、同种子的完整独立执行已重现三个最终路由树和质量指标；逐网决策与
最终连通性审计通过。全流程计时约为 ex5p 4216.6 秒、diffeq 5495.2 秒、
alu4 4527.1 秒，含父路由、两阶段修复、原生验证及显式审计，排除启动前源码
哈希预检。成本仍高；这不是不同种子或留出集结果，未关闭 G4，未建立 FPGA 加速。
见[三设计策略审计](work/native_refreshed_critical_policy_v1_20261016/independent_audit.json)。


完整重复与计时分别见[独立重复审计](work/native_instrumented_compound_repeat_review_20261016/independent_audit.json)
和[计时审计](work/native_instrumented_compound_timing_review_20261016/audit.json)。

相同三层原生图的静态/自适应迁移各五次重复已审查：两组均合法且组内可重复，
但均为 WL 12205、CPD 10.5998 ns、跨层边 839，未通过联合质量基线。自适应
背压事件 2233→804，远端影子读取 407075499→431550917，含验证平均耗时
1259.4→1501.3 秒，因此不能以背压下降宣称性能收益。
见[迁移配对审查](work/three_layer_migration_native_pair_review_20261016/independent_audit.json)。

提交核的新拆分通过 225 次 CPU 差分、75 次 RTL 调用及原生图 43 次提交/查询；
实际硬件 XO 的 LUT/FF/DSP 从 204708/163021/53 降至 170493/133506/41，
接口与估计时钟约束检查通过。后续物理结果见下文；上一集成版本存在 2827 个
未布通信号、2112 处节点重叠，不把资源下降视作布线成功。
见[实际 XO 对照审计](work/lean_start_actual_XO_comparison_20261017/audit.json)。

后续物理布线步骤已成功完成，完整 routed 报告确认 300 MHz 建立时序失败：
WNS -2.304 ns、52286 个失败端点；保持时序 WHS +0.006 ns。工具自动将内核
频率改为 177.3 MHz，不能视作原目标通过。部分位流及完整 xclbin 链接已成功，独立只读签核完成：586048 条可布线网全部
布通、布线错误为零；保持、脉宽、无严重 DRC、总线偏斜数值检查均通过，
建立时序失败。DRC 的 329 条 Warning/5 条 Advisory 与外部 IO 延迟缺项仍保留，
不视为无条件工程发布通过。见[最终独立审查](work/lean_start_routed_review_20261017/independent_audit.json)。见[300 MHz 失败归档](work/lean_start_300MHz_timing_failure_interim_20261017/audit.json)。
针对最差路径落在 traffic AXI 读缓冲控制链的观测，隔离读缓冲变体将读并发
16→1、最大读突发 16→2；75 次 C 差分及 Verilog 协同仿真通过。实际 XO
确认外部接口一致，LUT/FF 估计减少 2392/33，估计时钟不变；已开始串行物理
链接，尚无物理时序或吞吐收益。见[实际参数审查](work/traffic_read_buffer_actual_XO_review_20261017/audit.json)
和[RTL 审查](work/lean_start_traffic_read_buffer_RTL_20261017/independent_audit.json)。
相同 75 次调用的 RTL 总周期为 288945→315265（+9.11%），说明缩小缓冲存在
测试平台可见的延迟代价；不能仅凭面积下降宣称性能改善。见[周期对照审查](work/traffic_read_buffer_RTL_cycle_comparison_20261017/audit.json)。

CPU 隐式图过滤变体通过 7200 次随机差分和 400 张小图的逐步穷举检查；固定
ex5p 初始快照单网 59 个连接的 ABBA 测量为旧实现约 19.4 秒、新实现 2.9–3.1 秒，
搜索结果一致。三个开发用例的完整流程均已通过独立重放：两阶段决策、最终树和质量
均与参考执行相同，另有完整原生候选结果的严格逐步对照。ex5p、diffeq、alu4
全流程耗时分别为 4216.6→3556.4、5495.2→4867.3、4527.1→3957.4 秒，
约下降 15.7%、11.4%、12.6%。这是共享主机上的同配置单次比较，
不是统计性或 FPGA 加速证明。
见[完整三设计审查](work/native_implicit_compound_review_20261017/independent_audit.json)、
[严格决策对照](work/implicit_strict_decision_equivalence_20261017/audit.json)及
[计时审计](work/native_implicit_compound_timing_review_20261017/audit.json)。

保留集已按[预注册协议](experiments/reserved_validation_protocol_20261017.json)打开并执行。
15 个原生基线尝试中，apex2 五种子均合法；frisc、elliptic 各五次均因冻结架构
容量不足而在打包阶段失败。这些失败保留在分母中，不能作为候选算法质量失败，
也不能据此声称三设计泛化成立。
见[15 次基线独立审查](work/reserved_native_baselines_20261017/independent_audit.json)。
apex2 五种子的图转换往返、原生代价映射和边代价重建均已独立审查；
首个种子的完整两阶段修复也已独立重放，原生合法，线长 19372→17482
（-9.76%），CPD 10.8372→11.2084 ns（+3.43%），跨层次数不增加，
因此联合质量标准失败。第 2 个种子随后完成两阶段修复并通过独立重放：
线长 19322→18243（-5.58%），CPD 11.1249→11.1182 ns（改善 6.7 ps），
跨层次数不增加，联合质量标准通过。五种子现均完成独立审查，全部原生合法、线长及跨层次数不增加；
第 2/3/4 种子联合通过，第 1/5 种子因 CPD 退化失败。第 3/4 种子
分别为 WL 19132/18717、CPD 11.4118/11.5252 ns；第 5 种子为
17924/11.3248 ns，CPD 比基线增加 1.08%。因此不能宣称保留集时序不退化。
见[五种子完整汇总](work/reserved_apex2_five_seed_summary_20261017/audit.json)。
见[第 2 个种子修复审查](work/reserved_apex2_seed2_refinement_review_20261017/audit.json)。
见[首个种子修复审查](work/reserved_apex2_seed1_refinement_review_20261017/audit.json)。
本轮保持冻结算法与完整分母；后续改进须作为新的具名研究，不能覆盖本轮结果。

另行冻结的容量扩展研究已完成六次原生尝试（20×16、28×22，两种尺寸各三个设计，
种子 1、宽度 80）：apex2 两次均合法；frisc、elliptic 四次均通过打包后在固定
宽度下不可布通。两种较大尺寸仍不足以补齐这两个设计的本配置布线覆盖，
不推断其他通道宽度或拓扑也失败，也不替代原留出集。见[容量扩展独立审查](work/native_capacity_coverage_20261017/independent_audit.json)。

固定上述六组打包网表及布局后，另行冻结的宽度 160/320 研究已完成全部 12 项，
全部通过原生布线合法性及输入、命令、产物哈希审查。frisc、elliptic 在两种尺寸、
两种较大宽度下均合法。这只补齐种子 1 的原生基线覆盖，尚未验证 DieRoute 在这些
新图上的质量或性能；不能替代原保留集，也不能抹去宽度 80 的失败。
见[固定布局宽度研究审查](work/native_fixed_placement_width_coverage_20261017/independent_audit.json)。

上述 12 项现均完成图转换与原路由往返独立审计：累计 40,998,960 个节点、
77,798,718 条边逐项检查，原始与回写路由的源点、父子边、开关、终点引脚一致，
原生合法性、线长和 CPD 均保持不变。随后全部 12 项原生打印成本映射与转换
通过独立审计：核对 40,998,960 个节点成本和 77,798,718 条边，其余图结构、
延迟及任务字节保持不变。打印精度与整数舍入限制仍存在。全部 12 项父路由
评估已冻结启动，算法质量尚待完成后的原生验证与独立审查。
见[成本转换审查](work/width_coverage_native_costs_20261018/independent_audit.json)。
见[宽度研究往返审查](work/width_coverage_roundtrip_20261017/independent_audit.json)。

实际自适应迁移输出与 CPU 质量修复的组合已完成一次 ex5p 验证，独立审查通过：
最终原生合法，WL 11397、CPD 10.4526 ns、跨层边 991，最终树与串行复合修复
相同。这补上了该开发用例的组合质量证据；单独修复耗时约 3609.4 秒，不含
已归档父路由及其验证，不能据此宣称加速、五次组合重复或硬件发布完成。
见[组合独立审查](work/native_adaptive_compound_review_20261017/independent_audit.json)。

以下为先前开发阶段的归档结论；后续结果以本节上方及独立证据为准。


三设计通用单遍原生 STA 守护修复现已全部完成，独立审计重放逐网接受条件和
最终连通性通过：ex5p 为 11496 / 10.5304 ns / 999，diffeq 为
11336 / 7.74031 ns / 727，alu4 为 9422 / 10.3951 ns / 886
（依次为原生线长、CPD、跨层边数）。三例分别访问 613/1023/584 条网，
接受 56/60/112 次更新，原生验证调用 174/289/240 次。
diffeq 和 alu4 通过联合基线，ex5p 时序仍失败；本配置不采用，未关闭 G4。
这是单次 CPU 后处理开发实验，尚无重复、留出集或硬件加速结论。
见[三设计独立审计](work/native_slack_guided_net_repair_v1_20261015/independent_audit.json)。

通用单遍原生STA守护整网修复的ex5p阶段已完成并独立重放通过：613条网，
56次接受更新、174次原生验证；最终连通性/容量/逐网接受条件一致。线长
12205→11496、CPD10.5998→10.5304ns，跨层边999。相对基线11615/10.4531ns/999，
线长及跨层用量达标，但CPD仍失败，因此不采用。该单遍为单独计费的CPU后处理，
不构成硬件加速结论；其余设计仍在原冻结流程中，当前已进入diffeq。
见[ex5p完整阶段独立审计](work/native_slack_guided_net_repair_v1_20261015/ex5p_case_independent_audit.json)。

搜索内跨层预算已有隔离原生验证：共享树增量记账通过400个逐步穷举对照，
共享跨层边只计一次。在已归档检查点的首个跨层超限候选上，联合延迟/跨层约束
找到另一棵树，网线长82→75；完整设计VPR合法，总线长11643→11636，
CPD保持10.5998ns，总跨层边999等于基线上限。该结果说明事后拒绝会遗漏
预算内替代树；仍未通过联合质量基线，未改写正在运行的三设计v1实验。
见[隔离原生验证](work/first_crossing_rejection_repair_20261015/native_review/result.json)。

真实STA余量推导预算的修复也已完成：公式在运行前冻结，三个交换候选的全部
14种连接顺序形成6个不同完整路由，全部通过路径/容量/预算审计及原生VPR。
只改变让路网，其余612条网（包括目标网）保持；原生CPD与各自交换父路由一致，
线长最多减少15。最好on候选为12017/10.4694ns，仍未达到11615/10.4531ns基线，
因此不采用。时序余量来自每个实际候选的1920条routed0只读观测，不是猜测放宽比例；
它仍属于保守sink-block信息，最终结论依据完整设计STA。
见[STA预算修复解释](work/sb3_STA_budget_repair_native_20261015/interpretation.json)。

让路网的受约束线长修复已完成：采用精确原生节点长度、现有交换路径的逐连接
打包延迟上限及2M标签预算，三个候选的全部14种连接顺序均完成。独立审计确认
最终树和每条路径精确重现原交换结果，线长无改善；因此未重复运行原生VPR。
这只否定本次贪心构树/固定延迟上限方案，不证明全局Steiner最优或更宽预算无效。
见[14种修复独立审计](work/sb3_delay_bounded_displaced_repair_20261015/independent_audit.json)。

双网交换诊断已有原生结果：恢复版本保留原探针进程消失且无结果的异常，按已独立
核验的必要边界筛选18/20条owner，共38次私有整网重建及路径/容量审计通过。
其中3个目标连接达标候选均通过VPR原生检查，未参与交换的611条网完全保持。
各自父路由CPD改善47.6/47.6/126.4ps，但线长增加10/33/27、跨层边增加4/3/3。
最好候选线长12028、CPD10.4694ns，仍差于基线11615、10.4531ns，故不采用。
这些是指定ex5p目标的诊断，尚非通用调度策略或独立重复结论。
见[原生结果解释](work/sb3_ex5p_two_net_native_validation_v2_20261015/interpretation.json)。

压缩XRT已按冻结1800秒界限终止，实际1801.93秒；搜索七项及压缩输入匹配，
首次proposal无wait返回/异常，六项提交后状态缺失，独立终态判为未完成。
原四条任务保留检查通过。三核集成候选现已按既定串行策略开始物理链接。
见[压缩终态审计](work/native_dual_potential_XRT_pipeline_20261015/independent_outcome_audit.json)。

压缩 potential 的实际 XRT 搜索阶段现已完成：原完整图/2M标签/2M展开预算下，
43次展开、256条观察，七项搜索原始产物逐字节匹配金标准；运行日志实际选择
format2，91,975,784字节的压缩输入转储也匹配金标准。首次proposal已入队，
仍停留在wait-begin；尚无提交及42次查询通过，也没有完整已验证上传字节计数。
独立审计保存了日志快照，未改写运行中的日志或终态审计。
见[压缩XRT搜索阶段审计](work/native_dual_potential_XRT_search_stage_20261015/independent_audit.json)。

集成控制阶段候选的 worker、snapshot、commit 三项实际硬件 XO 编译均返回0。
新增独立审计核对原映像 ABI、打包源码、预处理文件及产物哈希；实际综合报告中，
worker/snapshot 比较辅助阶段均为2周期、II1、估计1.621ns，commit 的独立
start 辅助函数也存在。三核顶层估计均2.433ns；commit start 辅助函数总延迟为
undef，不能声称固定周期。物理链接等待压缩 XRT 独立终态审计，后续只读路由报告
和独立签核队列已启动；尚无该候选的布线时序或板上性能结论。
见[三核实际编译独立审计](work/native_integrated_control_compiled_audit_20261015/independent_audit.json)。

提交核另一个接近最差值的start分派控制路径已建立私有隔离变体：两种配置共150次
原命令CPU差分、各一次原生proposal/42次查询及六项最终状态差分通过；开启臂
75次Verilog协同仿真、数值时序预算和外部ABI也通过。估计周期仍2.433ns，
但LUT165286→204708、FF128235→163021、DSP41→53。后处理报告计数失败已
保留并只读恢复审计，没有重跑综合；尚无该变体的物理改善或采用结论。
见[RTL审计](work/native_commit_split_start_RTL_20261015/independent_audit.json)、
[原生CPU差分](work/native_commit_split_start_full_native_CPU_20261015/independent_audit.json)。

新两阶段未压缩XRT验证已达到冻结1800秒界限，实际1801.88秒后仅清理本次
新探针进程树，原四条任务保留。搜索七项原始产物匹配金标准，但首次op3停留
在wait-begin，未记录wait返回/异常，未产生六项提交后状态；不能认定端到端
通过或据此归因死锁。按冻结顺序，压缩potential映像现已开始串行链接。
见[独立终态审计](work/native_two_phase_identity_XRT_pipeline_20261015/independent_outcome_audit.json)。

snapshot最差读控制路径的私有比较阶段变体已完成初步验证：完整cost/hops/parent/edge
排序保持，辅助函数实际2周期/II1、估计1.621ns；两臂顶层均2.433ns≤有效预算
2.43309ns，外部290端口/79总线参数一致，增加41LUT/304FF。原10次Verilog
协同仿真和两个flag的完整图2M/2M顶层C-model七项金标准差分通过。
两臂均有未满足循环约束记录；尚无该变体的物理收益或采用结论。
另，新两阶段XRT映像的搜索七项原始产物已匹配金标准，但首次proposal仍在等待。
见[RTL审计](work/native_admission_compare_stage_RTL_20261015/independent_audit.json)、
[完整图CPU差分](work/native_admission_compare_stage_full_native_CPU_20261015/independent_audit.json)、
[XRT搜索阶段](work/native_two_phase_XRT_search_stage_20261015/independent_audit.json)。

两阶段物理链接现已返回0，映像哈希独立核验通过；原请求300MHz的正式报告
WNS−1.362ns、setup违例36121，不能视为时序通过。元数据DATA_CLK212MHz，
不是板上测量或调整后时钟签核。保留命名DCP的独立只读报告已完成：583626条网络全部布通，路由错误零；
hold/脉宽/数值bus-skew通过，但setup仍失败，DRC329Warning/5Advisory不视为豁免。
最差路径为snapshot边流水寄存器→scratchAXI读缓冲使能，数据延迟3.981ns，
布线占74.404%，10级逻辑。见[独立审计](work/two_phase_routed_independent_review_20261015/independent_audit.json)。
配套未压缩higher-g emulation映像也已链接并核验39指针HBM分组，完整图
XRT搜索—提交—42次查询验证已实际启动，保留2M/2M预算与1800秒保护界限，
尚无端到端终态通过。见
[物理链接终态](work/native_commit_two_phase_hw_20261015/manifest.json)、
[分组审计](work/native_two_phase_higher_g_hw_emu_20261015/group_audit/audit.json)、
[实际XRT运行](work/native_two_phase_identity_XRT_pipeline_20261015/manifest.json)。

完整策略图的静态跳数下界与排序四臂现已全部核验：原 coarse 下界的
lower/higher-g 展开为 229,746 / 58,069，identity-hop 下界为 1,907 / 43；
四条路径均为 42 边、代价 42，路径与全部导出观察独立回放通过。新下界逐边
核验 212,892,069 条允许边，源点值 42；准备需要 2.69 GB 数据、约 3,131 万 BFS
展开，不能把在线展开减少解释为端到端加速。43 次展开路径的 256 条版本读集
实际提交并查询 42 节点，43 次 flat/三银行逐字节差分及全部 341 棵树重计通过。
实际 worker/snapshot 顶层 C-model 的七项产物也匹配参考，新增等 f 排序夹具通过。
两模块已完成 HLS/Verilog 协同仿真并独立核验外部 RTL 接口及 AXI 参数保持一致；
300 MHz 仅为请求、2.433 ns 仅为 HLS 估计。新 hw_emu 映像已链接并通过 39 指针参数/HBM 分组审计，完整 XRT 搜索—提交—42 次查询验证
已启动；尚无此候选的终态执行通过或板上证据。运行保留原完整图、2M 标签和
2M 扩展上限，并预先冻结 1,800 秒功能验证保护界限。见
[四臂 CPU 审计](work/native_policy_identity_ordering_cpu_20261015/independent_audit.json)、
[顶层 C-model](work/native_identity_higher_g_top_cmodel_20261015/independent_audit.json)、
[HLS/RTL 审计](work/native_higher_g_hls_validation_20261015/independent_audit.json)。
平台证据见 [分组审计](work/native_higher_g_hw_emu_link_20261015/group_audit/audit.json)，
执行配置见 [完整 XRT 协议](work/native_identity_higher_g_xrt_pipeline_20261015/protocol.json)。
完整图 snapshot CU 已返回 found，43 次展开、256 条观察、路径/代价均为 42，
七项原始搜索产物逐字节匹配 CPU 金标准；同一共享 BO 上的完整提交/42 次查询
链路达到冻结的 1,800 秒保护界限，未完成端到端验收。仅新进程树被停止，
四条原任务保留，不能据此认定死锁。见 [XRT 搜索阶段审计](work/native_identity_higher_g_xrt_pipeline_20261015/search_stage_audit.json)。

提交内核失败检查点的路径诊断已核验：生成 FSM 为 2,496 位 one-hot，最差路径
从状态 2482 经 store 控制抵达 traffic AXI 读缓冲使能；5.235 ns 数据延迟中
布线占 77.515%，逻辑为 13 级。这仅定位该检查点的瓶颈，尚未证明改编码或
切分函数能够改善物理时序；本地 2022.2 的 `config_rtl` 帮助未列出 FSM 编码选项。
见 [路径与 RTL 审计](work/native_commit_fsm_path_diagnosis_20261015/independent_audit.json)。
在原 production 父版本上建立的私有窄错误状态变体（内部 uint64→uint8，外部
状态字保持 64 位）已通过 75 次逐字节差分；56 个错误入口均为状态码 0–8。
同一 3.333 ns 约束下的综合已完成：LUT 144,002→141,128、FF 114,224→109,936，
但估计周期 2.53571 ns 超出 2.43309 ns 有效预算（HLS 200-871），不采用；
75 次 Verilog 协同仿真已全部通过，290 条外部端口声明与 79 项总线参数
保持一致；功能通过不改变时序门槛失败结论。见
[CPU 审计](work/native_commit_narrow_error_variant_20261015/independent_audit.json)、
[HLS 协议](work/native_commit_narrow_error_hls_20261015/protocol.json)、
[综合阶段负面结果](work/native_commit_narrow_error_hls_20261015/synthesis_interim_audit.json)。
[终态 RTL 审计](work/native_commit_narrow_error_hls_20261015/independent_audit.json)已完成。
后续私有变体将原样分支终点/深度/代价比较提取到独立两周期函数，75 次 CPU
逐字节差分通过；综合确认 helper 为两周期/II=1，但顶层 2.51586 ns 仍超出
2.43309 ns 有效预算，不采用，未进入 RTL 或物理实现。见
[比较边界 CPU 审计](work/native_commit_branch_check_boundary_20261015/independent_audit.json)、
[综合协议](work/native_commit_branch_check_synthesis_20261015/protocol.json)。
[终态解释](work/native_commit_branch_check_synthesis_20261015/interpretation.json)保留负面结果。
后续改为从原 production 核提取六个完整命令阶段（保留 64 位错误状态），
逐段还原后与原源文件逐字节相同，75 次 CPU 差分通过；同约束综合已通过
有效时序预算，外部 290 端口/79 总线参数一致。顶层 FSM 从 3,503 位降至 151 位，
但 LUT 144,002→247,610、FF 114,224→197,444、DSP 35→61，面积代价明显。
独立新工程的 75 次 Verilog RTL 验证已全部通过并独立审计；尚无物理时序收益
或采用结论。
见 [六阶段审计](work/native_commit_phase_boundaries_20261015/independent_audit.json)、
[综合审计](work/native_commit_phase_synthesis_20261015/independent_audit.json)、
[RTL 终态审计](work/native_commit_phase_rtl_20261015/independent_audit.json)。
[面积增长审计](work/native_commit_phase_synthesis_20261015/area_growth_audit.json)显示
`locate` 在六阶段均有独立实例。两阶段验证/执行分组已通过 75 次 CPU 差分及
同约束综合：LUT 165,286、FF 128,235、DSP 41、顶层 FSM 145 位，外部接口保持
一致且无有效时序预算警告。75 次 Verilog RTL 调用和独立接口/综合审计已通过，尚无采用或物理收益结论。
见 [两阶段综合审计](work/native_commit_two_phase_synthesis_20261015/independent_audit.json)、
[RTL 终态审计](work/native_commit_two_phase_rtl_20261015/independent_audit.json)。
原 300 MHz 请求、配套 XO 和 HBM/SLR 映射的物理编译已完成，编译后
嵌入源码/ABI/HLS 检查通过，串行物理链接正在运行；见
[物理构建协议](work/native_commit_two_phase_hw_20261015/protocol.json)。
链接完成后的 [只读报告队列](work/two_phase_postlink_readonly_reports_20261015/protocol.json)
已启动等待：保存命名 DCP、核验前后哈希、独立报告时序/路由/DRC/bus-skew/资源
和 CU 时钟，并提取最终映像时钟元数据；这些报告仍须独立解释才能判断签核。
实际 XRT 搜索导出的路径在两阶段 CPU C-model 中完成一次提交/42 次查询，
43 次 guarded-bank 差分和六项最终状态匹配已审计金标准；这仍是 C-model 集成
证据；完整共享 BO XRT 链路的有界未完成终态见
[有界结果审计](work/native_identity_higher_g_xrt_pipeline_20261015/bounded_outcome_audit.json)。
后续独立诊断保持同一映像、完整图和 2M/2M 搜索预算，仅增加 BO、传输、内核
入队/等待/读回阶段标记；撤销日志改动可逐字节还原父主机源码。仍冻结 1,800 秒
保护界限，初始匿名余量须超过 32 GiB、低于 8 GiB 仅停止新诊断。该诊断已达到冻结保护界限，
再次未取得端到端通过。见
[阶段日志协议](work/native_identity_XRT_commit_stage_diagnostic_20261015/protocol.json)、
[源码审计](work/native_identity_XRT_commit_stage_diagnostic_20261015/logging_source_audit.json)。见
[参数/内存契约审计](work/native_XRT_commit_argument_contract_20261015/independent_audit.json)
核对 29 参数、15 项已记录 BO 范围及声明容量；图分组逻辑余量 58,360,408 字节。
终态日志记录所有提交准备和入队 API 返回，最后标记为首次 proposal（op3）的
`kernel_wait_begin`，未记录成功完成；见 [现场快照](work/native_XRT_first_commit_wait_observation_20261015/independent_audit.json)。
这仅定位主机等待位置，不证明设备侧进展或死锁。
[第二次有界终态审计](work/native_identity_XRT_commit_stage_diagnostic_20261015/independent_bounded_audit.json)
确认七项原始搜索产物再次匹配首轮和 CPU 金标准。完成标记位于 wait 状态检查
之后，缺少独立返回状态记录，故不推断精确设备状态或失败原因。

原等待映像的提交核新增独立组件诊断：紧凑 300 节点、三 owner、256 条读集和
42 节点路径，45 次初始化/启动/提交/查询 C/RTL 差分及结构重建通过。只修改
测试编组深度，39 个 HDL 文件中 9 个字节不同；保留所有运算、常量、接口和
参数的 token 比较确认仅为生成标识符的一一重命名，数值/时钟端口负控均拒绝。
这是原提交核的组件覆盖，不是两阶段物理候选或全图共享 BO 的通过证据。见
[45 次 RTL 审计](work/native_commit_42path_256reads_RTL_diagnostic_v2_20261015/independent_audit.json)、
[标识符审计](work/native_commit_large_traffic_RTL_identifier_audit_20261015/independent_audit.json)。

完整应用 C-model 计数显示 proposal 的 86 个新 scratch 键产生 7,099 次未命中
键比较（load 3,444、store 3,655），其余 owner 探测 341、读集二分 336、CSR
二分 114。计数器版本的 43 次差分与六项最终状态仍匹配金标准；这是逻辑循环
计数，不是 AXI 事务、周期或板上性能。见
[逻辑访问审计](work/native_commit_logical_access_profile_20261015/independent_audit.json)。
据此建立默认关闭的 256 位保守预筛选：否定答案才跳过扫描，可能存在时仍做
原始完整键比较；无容量截断，饱和退化为原扫描。开关两组各 75 次原用例、
各 43 次完整应用差分、20,000 次性质检查和 ASAN/UBSAN 通过；无计数器启用
版本的 43 次完整应用调用也通过。逻辑键比较 7,099→967，六项状态完全一致。
同 3.333 ns 约束的 75+45 次 RTL 验证全部通过，290 个端口声明及 79 个总线参数不变。
两组综合估计均为 2.503 ns，超过精确有效预算 2.43309 ns（尽管日志无时序警告），因此不采用。
独立同用例仿真总周期分别为 301615→230705、817772→324622；不代表全图 XRT 或板上加速。见
[数值时序审计](work/native_commit_key_filter_HLS_20261015/exact_timing_audit.json)、
[RTL 审计](work/native_commit_key_filter_HLS_20261015/independent_audit.json)、
[CPU 审计](work/native_commit_key_filter_variant_20261015/independent_audit.json)、
[无计数器完整应用](work/native_commit_key_filter_variant_20261015/plain_native_audit.json)、
[HLS 协议](work/native_commit_key_filter_HLS_20261015/protocol.json)。
[应用数据提交审计](work/native_two_phase_XRT_path_CPU_commit_20261015/independent_audit.json)。

两阶段结构与同一预筛选的组合也完成筛选：开关两组 150 次 CPU 用例、
86 次完整原生图提交/查询差分通过，两组各六项最终状态匹配金标准。
但综合估计仍为 2.503 ns，超过 2.43309 ns 有效预算，LUT/FF 为 175645/136562；
函数分阶段未消除本候选的数值时序失败，因此不启动其 RTL/物理构建。首次
检查缺测试头文件的失败记录保留，v2 仅补齐原有头文件。见
[组合综合审计](work/native_commit_two_phase_key_filter_screen_v2_20261015/independent_audit.json)、
[完整原生图审计](work/native_two_phase_filter_full_native_CPU_20261015/independent_audit.json)。

进一步隔离位图查询的两拍流水实验：150 次 CPU 差分通过，局部查询函数
确实达到延迟 2、II=1，估计 1.165 ns，外部接口仍为 290 个端口声明及 79 个总线参数。
但整体估计恶化为 2.586 ns，LUT/FF 为 173211/139318，因此同样不采用。
层次报告仅定位原 2.503 ns 在执行阶段，尚不能证明具体操作是根因。见
[层次定位](work/native_filter_timing_hierarchy_diagnosis_20261015/independent_audit.json)、
[流水候选时序](work/native_commit_filter_probe_pipeline_screen_20261015/independent_audit.json)、
[局部流水与接口审计](work/native_commit_filter_probe_pipeline_screen_20261015/structure_audit.json)。

势函数存储的无损压缩已完成全图检查：当前固定原生任务的 91975782 个
势函数值均 ≤42。8 位打包与独立逐字节解码逐节点匹配原 64 位值，任何 >255
值会明确拒绝，未改变原启发值或搜索预算。逻辑载荷 735806256→91975784 字节，
节省 643830472 字节；沿用原 4 KiB 静态对齐模型时，图分组余量
58347520→702177280 字节。这只是存储格式候选，尚未接入内核/主机或 XRT，
不能推导 HBM 事务或性能收益；原 31308452 节点/108050406 边 BFS 预处理仍需计入。见
[全图压缩审计](work/native_potential8_lossless_storage_20261015/independent_audit.json)。
默认关闭的解码器及主机编码已通过两组完整原生图实际 top C-model，
各七项原始搜索输出匹配金标准，启用组的输入文件也逐字节匹配全图压缩审计。
4099 个值、每组 20000 次覆盖写、边界拒绝、保护字、ASAN/UBSAN 和非法开关检查通过。
旧定向用例含 `UINT64_MAX`，因此当前原型不能直接替换所有输入；下一版须保留
完整 64 位路径，只对全量范围已验证的任务启用紧凑格式。该旧原型仅作为阶段证据保留。见
[C-model 审计](work/native_potential8_kernel_Cmodel_20261015/independent_audit.json)、
[兼容格式协议](experiments/native_potential_format_protocol_v1.json)。
后续双格式版本已实现完整 64 位回退：格式 1 保留所有原数值，只有全量
检查 ≤255 才编码并选格式 2；开关关闭仍只允许原 0/1，启用后仅额外允许 2。
原封装器会拒绝 >1，故 v2 协议纠正了 v1 对其他非零值的假设。
开关两组各 10 次原定向用例及完整原生图实际 top 通过，各七项原始输出
匹配金标准；共享主机准备函数对 256/UINT64_MAX 保持完整宽格式。
4099 项宽/窄值性质、格式边界与 ASAN/UBSAN 通过。保留原 10 次并新增
15 次紧凑格式用例的 CPU 预检也通过。同 3.333 ns 的 HLS/Verilog 共 25 次
调用全部通过；综合估计 2.433 ns ≤有效预算 2.43309 ns，生成的 290 个端口
声明及 79 个总线参数与父版本一致。资源为 99295 LUT/64545 FF/12 DSP。
尚无新镜像、XRT、路由时序或性能通过结论。见
[HLS/RTL 审计](work/native_potential_dual_format_HLS_20261015/independent_audit.json)、
[双格式 CPU 审计](work/native_potential_dual_format_Cmodel_20261015/independent_audit.json)、
[修正协议](experiments/native_potential_format_protocol_v2.json)、
[HLS 协议](work/native_potential_dual_format_HLS_20261015/protocol.json)。
双格式 snapshot 的 hw_emu 编译已成功，估计 2.433 ns、7 个端口/15 个参数
与父 snapshot 一致。首版检查器错误要求 XO 嵌入头文件，已保留失败记录；
新审计复用了同一次 XO，核对嵌入 CPP、冻结头文件及实际保存的预处理双格式逻辑，
没有重编。新镜像复用原 worker 与两阶段 commit，须等待未压缩 XRT 对照
完成并审计后才链接，且所有链接继续由全局锁串行执行。
新 XRT 主机编译及缺少能力确认的拒绝预检通过：实际检查 212892069 条
原生允许边，选择格式 2/91975784 字节后，在设备上下文创建前退出。
完整运行队列须验证镜像能力、分组和哈希；成功仍要求原 13 项原始结果
加打包输入，共 14 项匹配，预算和 1800 秒时限不变。尚无新镜像运行或性能结论。见
[编译产物修正审计](work/native_dual_potential_hw_emu_review_v2_20261015/compiled_XO_review.json)、
[主机预检审计](work/native_dual_potential_XRT_pipeline_20261015/host_preflight_audit.json)、
[控制顺序构建协议](work/native_dual_potential_hw_emu_review_v2_20261015/protocol.json)、
[双格式运行协议](work/native_dual_potential_XRT_pipeline_20261015/protocol.json)。

两阶段提交核的联合 hw_emu 镜像已启动构建：只重新编译提交核，复用已审计、
字节不变的 higher-g worker/snapshot XO 与原 HBM 映射；数值综合预算不放宽。
链接须等待全局串行锁，编译后的嵌入源码、ABI 以及最终分组分别复核。
这是后续完整原生图 XRT 提交验证的准备，尚无共享 BO 提交或性能通过结论。见
[两阶段联合仿真构建协议](work/native_two_phase_higher_g_hw_emu_20261015/protocol.json)。
提交核 hw_emu 编译已通过：嵌入源码及 7 个端口/29 个参数匹配，估计 2.433 ns；
当前等待物理链接释放全局锁。完整原生图 XRT 队列已准备，待镜像和分组审计
完成后才启动，保持 2M 标签/2M 扩展、1800 秒和内存门限。主机仅补充
`wait()` 返回状态与异常标记，反向还原后与旧日志诊断主机完全一致；
成功验收要求 1 次提交、42 次查询与 13 项搜索/最终状态原始文件一致。见
[主机预检](work/native_two_phase_identity_XRT_pipeline_20261015/host_preflight.json)、
[XRT 运行协议](work/native_two_phase_identity_XRT_pipeline_20261015/protocol.json)。

两阶段物理候选已增加独立报告验收队列，等待原只读报告完成后核对
请求 300 MHz 的 setup/hold/pulse、完整路由、DRC、总线约束及内部时钟约束。
最终时钟拓扑单独记录，不能据链接成功、自动降频或拓扑名称判定 CU 达到 300 MHz。
归档负 WNS、缺失汇总和部分布线输入已用于检查解析行为；最终位流与保留
检查点对应关系、调整时钟后的签核及上板性能仍需独立证据。见
[独立验收协议](work/two_phase_routed_independent_review_20261015/protocol.json)。

原生 QoR 的零种子权重消融已全部完成并独立审计：仅 ex5p/diffeq/alu4，
固定剩余层尾界开启及 cost scale=256，每例一次、最多 30 轮、至少 3 次 STA。
输入、源码及其余环境均与已完成的权重 128 对照一致；零权重仅清除树累计延迟
的种子初始代价，保留种子顶点/深度、边时序成本及原生 STA。
三例均原生合法，但联合门槛仅 1/3 通过（权重 128 为 2/3）：
ex5p 线长 11752、CPD 11.0258 ns、模型跨层边 811；
diffeq 11404/7.73181 ns/690；alu4 9978/10.854 ns/661。
相对权重 128，三例线长均下降，但 ex5p 和 alu4 的 CPD 更差且超过原生基线。
因此零种子权重不能解决联合 QoR 退化，不采用；无重复或留出集结论。见
[协议](work/rr_remaining_tail_zero_seed_ablation_20261015/protocol.json)、
[配置审计](work/rr_remaining_tail_zero_seed_ablation_20261015/configuration_audit.json)、
[三例审计](work/rr_remaining_tail_zero_seed_ablation_20261015/independent_audit.json)、
[固定对照比较](work/rr_remaining_tail_zero_seed_ablation_20261015/comparison_audit.json)、
[结论](work/rr_remaining_tail_zero_seed_ablation_20261015/interpretation.json)。
原 ex5p 阶段审计仍保留，终态三例审计为当前完整结论。

ex5p 的原生 STA 路径已重新绑定并对齐：对基线、权重 128/0 的固定合法路由
使用同一冻结 VPR 和原 `--analysis` 命令重分析，CPD 精确复现，三份路径报告
也与旧报告逐字节一致。63 个输出端点中，权重 128/0 分别有 50/59 个打印
到达时间更高；基线最差端点为 `o_41`，两候选切换到 `o_56`，起点也改变。
相同打印弧 `[3355].out[0] → [3663].in[1]` 的增量由 0.762 ns 变为
1.149/1.176 ns。这是 0.001 ns 分辨率的路径描述，不能据此认定单独恢复此弧
即可修复全局 CPD、合法性或联合门槛。见
[路径审计](work/sb_ex5p_native_STA_path_alignment_20261015/independent_audit.json)、
[结论](work/sb_ex5p_native_STA_path_alignment_20261015/interpretation.json)、
[端点时序图](paper/figures/ex5p_native_endpoint_arrivals.png)、
[可导出 PDF](paper/figures/ex5p_native_endpoint_arrivals.pdf)。

逻辑弧到 RR 路径的只读映射已完成：三份路由均对应 net 138、task 895，
SOURCE 43804 → SINK 14256；映射核验了打包端口旋转与等价输入引脚类别。
基线/权重128/权重0的原生通道长度单位为 11/21/22，模型层间跨越均为 2；
打包 RR 边延迟和为 567/954/981 ps，后两项与末轮 STA 输入一致。
打印弧与该和的差均为 195 ps，仅为三份路径的观察，不作为普适时序分解。
容量审计按冻结提交模型排除 SOURCE，逐项重建两候选全部 336312 个资源占用；
精确基线路径分别有 5/8 个节点被其他 net 占满。因此固定其他 net 时不能
只恢复 net138 的这条路径；这不排除其他路径，也不证明联合重路由的收益。
见 [RR 绑定](work/sb_ex5p_critical_arc_RR_binding_v5_20261015/independent_audit.json)、
[容量审计](work/sb_ex5p_critical_route_capacity_v3_20261015/independent_audit.json)。

末轮关键度已进一步区分：task895 在权重128/0的输入为61942/64880，
原始 STA 输出均65535，但冻结主机会将输出封顶64880。控制器在合法、无超用且
达到最少 timing 轮数后允许结束；未启用的反馈策略要求从阈值下方跨入，故
两条已观察末轮轨迹只有权重128满足跨入条件。启用反馈会改变更早轨迹及每net
一次的使用历史，不能由此推断实际候选资格或修复效果。旧反馈对照使用两层
ex5p/scale1，不是本次三层/scale256的直接对照。见
[逐轮记录](work/sb_ex5p_task895_timing_trajectory_20261015/independent_audit.json)、
[停止与关键度策略审计](work/sb_ex5p_terminal_timing_policy_20261015/independent_audit.json)。

三层固定反馈对照已完成六次串行运行及独立审计：三个新关闭臂复现归档结果，
开启臂全部通过资源/版本/代价/反馈回放和原生合法性验证。关闭/开启均仅2/3
通过原联合门槛，不采用。ex5p线长12205→12001、CPD10.5998→10.5958ns，
仍同时超过原基线；diffeq保持11584/7.74031ns，19条反馈均属普通重路由；
alu4由10083/10.2653ns变为10134/10.3486ns，质量略差但仍通过该用例门槛。
每臂一次，保持 remaining-tail1、seed128、scale256、max30/minSTA3及阈值0/64880；
无heldout或板上结论。见
[完整独立审计](work/sb3_fixed_feedback_pair_20261015/independent_audit.json)、
[成对比较](work/sb3_fixed_feedback_pair_20261015/comparison_audit.json)、
[解释](work/sb3_fixed_feedback_pair_20261015/interpretation.json)。

ex5p 的只读容量最短延迟诊断进一步固定其他612个net、释放net138全部占用，
在不限制corridor/代价/跳数的打包图上计算task895的乐观最优值：反馈关闭644ps、
开启729ps，仍高于基线567ps。独立验证器不重跑最短路，而是核验保存的全部
可达边距离不等式及达到该值的可行路径，确认两个最优值。因此固定其他net时，
连这一放松问题也无法恢复该连接的基线打包延迟；这不证明全局CPD无法恢复，
也不证明整棵net138树可实现这些局部最优路径。没有向实际路由器提供oracle输入。
见 [诊断](work/sb3_ex5p_capacity_delay_bound_20261015/independent_audit.json)、
[独立证书验证](work/sb3_ex5p_capacity_delay_bound_20261015/certificate_audit.json)。

上述567ps目标的必要首个占用边界已只读枚举：关闭/开启臂分别31/29个节点，
owner并集涉及18/20个其他net。任意达到目标的路径首次遇到的占用节点必在该集合，
但并集不是最小割，不表示必须移动全部这些net，也不证明任一释放集合足以修复。
该诊断不用于按net ID选择算法规则或向路由器注入路径。见
[竞争边界诊断](work/sb3_ex5p_delay_frontier_20261015/independent_audit.json)。

原生长度与 indexed base cost 已进一步区分：同一 SB3/cw80 开发架构的三个
用例中，各有 271224 个 `Direction::NONE` CHANX 节点，原生线长为零，
但原生 segment 1 的导出 base cost 为 312。每例实际输入的 561561 条边均
逐项匹配其目标节点的原生 indexed price，其中 180816 条指向这些零长度节点。
这是原生资源价格与原生线长统计的不同语义，不是发现了转换错误；不能为
改善线长而擅自清零这些代价，也不能据此归因 CPD 退化。见
[零长度与原生价格检查](work/native_zero_length_indexed_cost_profile_20261015/independent_audit.json)。

逐网线长分解已按冻结原生源码核验：`Direction::NONE` 通道原生长度为零，
其余 CHANX/CHANY 为 `1+dx+dy`。旧二维跨度公式会误计零长度通道；精确规则
现已还原全部六次原生 WL。ex5p 两档真实净增加为 640/590（旧代理 298/270），
分别来自总增加 1,691/1,664 与总减少 1,051/1,074。六次观测的旧代理偏差
均等于两倍模型 crossing 数，但这不是通用定理或安全替换策略。原生 QoR
数值及不采用结论保持不变。见 [逐网分解](work/sb_precision_per_net_wirelength_v3_20261015/independent_audit.json)、
[口径解释](work/sb_precision_per_net_wirelength_v3_20261015/interpretation.json)。

精度六次对照已全数完成并通过独立终态审计，fresh scale1 累计 115 项父产物
比较匹配。两档精度都只通过 2/3 开发例，ex5p 均失败；diffeq scale256 为
WL=11,584 / CPD=7.74031 ns，alu4 为 10,083 / 10.2653 ns。没有全开发集候选，
不采用，保留集未打开。见
[六次精度结论](work/rr_remaining_tail_precision_development_v2_20261015/interpretation.json)。

常量 zero 硬件候选已成功链接，但独立保留 routed checkpoint 的 300 MHz
setup 失败：WNS=-2.413 ns、TNS=-38,255.922 ns、60,945 个失败端点；hold/pulse
未见失败，布线错误为零。执行日志记录自动降频，最终 DATA_CLK 元数据为
174 MHz（另一 KERNEL_CLK=500、hbm_aclk=403）；不是板上频率或调整后独立签核。
该次 WNS/名义 DATA 时钟较父记录 -2.014 / 187 更差，单次实现不作因果归因，
候选不采用。最差路径从 net_commit FSM reg[2481] 到 traffic AXI FIFO RAM 使能。
未证明命名 DCP 与最终 bitstream 完全对应。见
[链接终态与时序审计](work/const_zero_final_clock_metadata_20261015/independent_audit.json)。

隔离的默认关闭“同 f 优先较大 g”队列候选已完成 CPU 对照：两档各通过
40,000 次队列操作及 4,000 次独立 Dijkstra 加权搜索核对，启用档 ASAN/UBSAN
通过，默认档七项原始产物匹配父基线。原完整任务展开 229,746→58,069，观察
862,428→236,636，仍为 42 边/代价 42；新路径与父路径不同，路径及全部导出
观察独立回放通过。这是单任务搜索工作量改善，不是 wall time、板上或通用 QoR 收益。
新路径已实际提交到 C-model：43 次调用中，受保护 flat 核与三独立带 guard 的
owner 数组逐字节一致，独立重计全部 341 棵 net tree/资源/版本及 revision 通过。
当前不采用，未构建新 HLS/XRT 映像；更强静态跳数下界两臂仍未实现。见
[排序对照审计](work/native_higher_g_tie_variant_20261015/independent_audit.json)、
[新路径提交差分](work/native_higher_g_commit_differential_20261015/independent_audit.json)。

完整 CPU 搜索的优先级插桩已与基线七项原始产物逐字节一致：229,746 次展开中，
171,901 次（74.8%）的 f 等于目标代价 42，另有 57,845 次 f 更低。
原 quotient 源点下界为 36；同分排序无法消除所有较低 f 展开。已制定隔离 CPU
排序/静态跳数下界对照，尚未启动，不表示改进或采用。见
[优先级剖面](work/native_fullgraph_cpu_priority_profile_20261015/independent_audit.json)。

16 次展开的完整工作区 hw_emu 已正常结束，result、metadata 及 63 条有序
观察与 CPU 参考逐字节一致；snapshot 入队和等待墙钟约 154 秒，仅是共享宿主
仿真开销，不能推算板上性能或按展开次数外推。两次展开探针此前也已返回。
CPU 完整搜索的六项产物复现旧 C-model 基线；既有 flat C-model 提交终态用
本次产物重新核对全部 341 棵 net tree 通过，不是新的三银行 XRT 提交证据。
见 [16 次匹配核验](work/native_sharded_quotient_budget16_diagnostic_20261015/independent_audit.json)、
[既有基线复现](work/native_fullgraph_cpu_full_search_20261015/prior_baseline_reconciliation.json)。

ex5p 精度两臂已完成独立阶段审计：scale1/256 均九轮原生合法；256 的
WL=12,205、CPD=10.5998 ns、模型跨层边 839，较 scale1 的 12,255 / 10.8661 ns
改善 WL/CPD，但仍高于原生 11,615 / 10.4531 ns。两臂联合质量均失败，不能采用。
六次对照继续按已冻结协议推进，尚待完整终态审计。见
[ex5p 精度阶段核验](work/sb_ex5p_remaining_tail_precision_interim_20261015/independent_audit.json)。

原完整图、原源/目标、quotient 和 2,097,152 次展开上限的同源 CPU 搜索已找到
42 边、代价 42 的路径，共展开 229,746 次。独立核对 CSR/PIP、保护规则、
树连接深度及路径代价；全部 862,428 条观察与冻结 owner shards 一致。
11 个实际输入载荷也与更早冻结绑定复核一致。路径 mask4→共享 mask6→mask2，
需一次抽象 die 切换；全部观察为 absent，未覆盖该路径上的拥塞竞争。
这不是 XRT 执行、提交闭环、物理 SLL 或板上性能证明。见
[完整 CPU 路径核验](work/native_fullgraph_cpu_full_search_20261015/independent_audit.json)、
[全 journal 核验](work/native_fullgraph_cpu_full_search_20261015/journal_authority_audit.json)。

256 次展开 hw_emu 探针达到预先声明的 600 秒上限，没有 snapshot 返回；
仅停止该诊断进程及其子进程，原四项长任务保留。不能据此断言死锁。
两次展开的相同完整工作区诊断现已启动，以定位首步之后的行为。见
[256 次诊断终态](work/native_sharded_quotient_budget256_diagnostic_20261015/bounded_outcome_review.json)。

精度交互六次对照已由独立 v2 链实际启动：三例固定 SB3/cw80、seed128、
remaining_tail=1，仅 scale1/256 改变，fresh scale1 必须匹配已完成父产物。
独立回放显式传入各臂 scale，固定 STA min3/max30，完整终态审计已排队。
首臂 ex5p_scale1 路由进程已确认；v1 缺少 recipe 支持链接，在路由前失败，
产物保留，不计作实验结果。见
[精度实验启动记录](work/rr_remaining_tail_precision_development_v2_20261015/launch_receipt.json)。

新增 ex5p 最终路径的无拥塞基础代价分量舍入剖面：16,413 次路径边经过中，
14,493 次基础代价为正；其中 123 次在 scale=1 下该分量为零，涉及 44 条连接，
scale=256 能保留这些分量。这不是完整边代价为零，也不是历史搜索评分或失败
因果证明；历史 scale256 负结果保留。已据此写出固定三例、seed128 的精度交互
设计，尚未启动。见 [剖面与范围](work/sb_remaining_tail_cost_quantization_profile_20261015/audit.json)。

加载 quotient 的匹配大工作区探针也已正常返回：上传核验 4,482,650,920 字节，
seed 与单步 snapshot 均完成，预算状态 2、expanded=1，authority 保持检查通过。
与不加载 quotient 的探针返回 result 字节相同。两者仅证明各自初始化和首步可执行，
不能证明原长任务进度或完整路径/commit。自动审计首次因源码副本归档缺失失败，
补齐后相同审计器通过，仿真未重跑。见
[quotient 对照结论](work/native_sharded_quotient_budget1_diagnostic_20261015/paired_interpretation.json)。

六次剩余尾部 seed 权重对照现已全部结束并通过独立审计。128 权重通过
2/3 个开发例，256 权重仅通过 1/3；ex5p 两臂均失败，alu4 的 256 权重
线长为 11,247，高于原生 10,620。256 在三例均降低观察到的 CPD，但同时
增加线长和模型跨层边，不能采用为通用改进；每臂仅一次，保留集未打开。
见 [完整权重结论](work/rr_remaining_tail_seed_weight_development_v2_20261015/interpretation.json)。

全 CSR 大工作区 hw_emu 诊断已正常返回：2,097,152 标签、2 GiB journal、
不加载 quotient、固定仅一次 expansion，seed 和 snapshot 均完成，返回预期
预算状态 2，authority 保持检查通过。空表 lookup 首个空槽即返回，源码不支持
“seed 必须扫描全部容量”的解释。此探针没有完成完整跨 die 路径或 commit，
也没有证明原长任务的进度或死锁；148.32 秒包含初始化和传输，不作性能推算。
见 [大工作区独立核验](work/native_sharded_large_workspace_budget1_diagnostic_20261015/independent_audit.json)。

六次三层开发集对照已全部结束并通过独立审计。剩余尾部候选在 diffeq、alu4
分别六/八轮原生合法并通过各自单次门槛；alu4 为 WL=10,158、CPD=10.2458 ns、
跨层树边 707（原生 10,620 / 10.3971 ns / 886）。原分层两臂均 30 轮容量失败；
alu4 flat 的 CPD=10.4351 ns 超门槛。结合 ex5p 已完成 pilot，候选三例均合法，
但仅两例通过质量，仍不采用。三例结果已绘成各自原生基线归一化图，不能作
跨案例 Pareto 排序。六次 128/256 权重对照已在原六臂审计成功后自动启动，
当前运行 ex5p fresh128 控制。见
[六臂终态审计](work/sb_three_layer_development_matched_20261015/independent_audit.json)、
[三例结论](work/sb_three_layer_development_matched_20261015/interpretation.json)、
[三例质量图](paper/figures/sb_development_quality.png)。

alu4 原分层臂已在 30 轮后以容量未收敛结束：28 个超用通道全部在中间层
（13 CHANX、15 CHANY），涉及 69 个 net，基础代价均为正。完整 30 轮资源/
版本/代价回放及树审计通过，连接搜索失败数为 0，最终字节一致。
alu4 剩余尾部候选已由原监督队列启动。三例原分层臂分别留下 15/24/28 个
中间层超用资源，尚不能据此证明单一因果；非法路由不作原生 QoR 比较。见
[alu4 超用剖面](work/sb_alu4_legacy_nonconvergence_profile_20261015/audit.json) 和
[完整失败回放](work/sb_alu4_legacy_nonconvergence_profile_20261015/lineage_review.json)。

原生延迟校准已扩展到另外两个开发例的已完成合法路由：diffeq remaining_tail
2,073 条连接、alu4 flat 1,987 条连接均独立重算 packed 路径并与原生 routed=0
结果核对，最大连接误差均为 2 ps。diffeq CPD 两侧均 7,742 ps；alu4 原生
10,435 ps、局部延迟输入 10,434 ps。加上 ex5p，三个已观察最终路由累计
5,980 条连接，最大 CPD 差 1 ps；并非所有路由/迭代或商业图校准完成。见
[新增两例校准](work/sb_development_native_delay_calibration_20261015/independent_audit.json)。

diffeq 三臂已完成独立阶段核验：flat 七轮原生合法，WL=11,503、CPD=7.73457 ns、
模型跨层树边 702；原分层臂 30 轮后仍超用 24 个资源；剩余尾部候选六轮合法，
WL=11,392、CPD=7.74186 ns、跨层边 690。本例原生基线为 13,004 / 7.76709 ns /
727 条跨层树边，因此 flat 和候选通过本例单次门槛，但候选 CPD 略高于 flat，
且仍有 ex5p 质量失败，不能采用为通用配置。alu4 分层对照仍在运行。见
[diffeq 三臂阶段审计](work/sb_diffeq_three_arm_interim_review_20261015/independent_audit.json)。

新尾部算法的 seed 权重交互已冻结并排队：ex5p/diffeq/alu4 × 128/256，各一次，
只有权重变化，固定原 30 轮上限，fresh128 必须匹配已完成父实验产物。
依据是当前 seed 上游延迟系数为 128/256，而原生 VPR 为完整 criticality×Tdel；
旧二层 fanout-serial 全权重负结果保留，不假定新组合有益。队列等待当前六臂
完整独立审计后才启动，保留集未打开。初版等待器的退出捕获问题在任何新路由
前发现并取消，仅 v2 队列接管；没有重复实验或参数变化。见
[权重匹配参数审计](work/rr_remaining_tail_seed_weight_development_v2_20261015/launch_audit.json)、
[队列状态](work/rr_remaining_tail_seed_weight_development_v2_20261015/queue.json)。

常量 zero 硬件候选已完成综合、进入实现阶段，原链接进程继续运行。新增归档
生成脚本顺序：route_design → route-post hook → routed DCP → PLATFORM_WRAPPER
属性 → bitstream-pre 自动频率处理 → partial bitstream。平台 postroute hook
实际是无尾换行的 12 字节 report_power；第一次误按零行数认作空文件的静态
检查已保留并纠正。命名 routed DCP 仍早于后续属性/时钟处理，不能据此认证
最终映像或 300 MHz；最终需结合执行日志及报告。见
[脚本顺序审计](work/const_zero_implementation_stage_order_20261015/audit.json) 和
[实现启动日志快照](work/const_zero_implementation_stage_order_20261015/implementation_start_receipt.json)。

diffeq 的原分层臂已达到固定 30 轮上限，legal=false、fallback=0，仍有
24 个超用资源；原生身份/容量/层号与 net 成员重计核验显示全部位于中间层
（14 CHANX、10 CHANY），涉及 63 个 net。基础代价均为正（96 或 312），
不能归因于零基础代价。这是另一个容量未收敛实例，尚不构成失败因果证明；
完整 30 轮版本/代价回放及树审计已通过，最终资源/代价字节一致；同输入的
剩余尾部候选已启动，alu4 对照尚未完成。
见 [diffeq 超用剖面](work/sb_diffeq_legacy_nonconvergence_profile_20261015/audit.json)。

同一三层 ex5p 候选最终路由的原生延迟校准已完成：使用冻结 VPR routed=0
接口读取真实 net_delay，不覆盖延迟；逐 task/source/sink 核对 1,920 条连接，
并独立按最终 packed 路径重算局部延迟。1,266 条在整数 ps 精度下相等，全部
误差在 −2..+2 ps；两种延迟输入的 CPD 均为 10,866 ps，criticality_q 最大差
32、slack 最大差 5 ps；51 条零延迟在两侧一致。这不支持把本次最终路由的
约 0.4 ns CPD 退化简单归因于大的延迟换算误差，但不证明其他路由或完整反馈
循环均等价，也不排除其他因果。见
[同路由延迟校准](work/sb_remaining_tail_native_delay_calibration_20261015/independent_audit.json)。

三层开发集匹配对照已启动：diffeq、alu4 各运行 flat、legacy_downstream、
remaining_tail 一次，共六次；同一冻结二进制、每例相同 placement/完整图/原生
代价及参数，固定最多 30 轮。已知容量未收敛会显式回放，未知异常停止队列；
终态独立审计队列也已启动。当前首个 diffeq flat 臂七轮原生合法，WL=11,503、
CPD=7.73457 ns，低于本例三层原生基线 13,004 / 7.76709 ns，模型跨层树边
702。其余臂尚未完成；这不是分层候选或全开发集通过，也不是五次重复。见
[匹配参数审计](work/sb_three_layer_development_matched_20261015/launch_audit.json)、
[阶段结果](work/sb_three_layer_development_matched_20261015/partial_result.json) 和
[终态审计队列](work/sb_three_layer_development_matched_20261015/review_queue.json)。

剩余分层尾部候选已完成三层原生 pilot 和终态审计：九轮合法、零超用、无
fallback，但 WL=12,255（较原生基线 +5.51%）、CPD=10.8661 ns（+3.95%），
联合质量门槛失败，不采用。模型跨层树边 999→828；也不能抵消 WL/CPD 退化。
516 项当前证据文件哈希及原生打印指标已复核。父分层臂曾在 30 轮后保留
15 个超用资源；这里只说明这次候选收敛，不证明通用改善或板上收益。见
[候选终态结论](work/rr_remaining_layer_tail_variant_20261015/interpretation.json)。

新增 diffeq/alu4 的完整图转换、不改树原生回写也已完成独立核验：累计
672,624 个节点记录、1,123,122 条有向边，树 parent/child、switch、sink pin
身份及各自原生 WL/CPD 保持一致。两例新鲜原生 indexed cost 导出/重基现已
完成，独立核对全部 672,624 个节点代价及 1,123,122 条边；其余字段不变。
三层开发集匹配算法对照仍待执行。见
[转换回写审计](work/sb_development_roundtrip_preflight_20261015/independent_audit.json) 和
[原生代价审计](work/sb_development_native_indexed_costs_20261015/independent_audit.json)。

现有开发集 diffeq、alu4 的三层 switchblock 原生基线已完成 FULL pack/place/route
并独立核验。相同固定每层 13×10、cw80、seed1 下，diffeq WL=13,004、
CPD=7.76709 ns；alu4 WL=10,620、CPD=10.3971 ns。两者 RR 图均与 ex5p
逐字节相同（336,312 节点、561,561 边，含 90,408 孤立记录），各保留 220 条
missing-fanin 诊断；packed 类型仅 LAB/IO，仍非异构工作负载覆盖或 DieRoute
质量结果。完整图转换和原生不改树回写预检已启动，验证集未打开。见
[新增开发基线](work/native_sb_three_layer_development_20261015/independent_audit.json) 和
[转换预检状态](work/sb_development_roundtrip_preflight_20261015/manifest.json)。

剩余分层尾部候选新增 8 项 proposal/commit 检查并通过 ASAN/UBSAN：成功及
跳数受限失败搜索均记录未选中中间层资源的版本，读取日志不重复；改变该
off-path 版本后提交返回 stale，权威资源字节不变。这是特定 fixture 的事务
检查，尚非全部 API 读取覆盖或硬件一致性证明。原生 pilot 的单一终态审计队列
已运行，合法时核验 QoR，不收敛时核验失败树和完整资源/版本/代价回放。
见 [读取日志检查](work/rr_remaining_layer_tail_variant_20261015/journal_audit.json) 和
[终态审计队列](work/rr_remaining_layer_tail_variant_20261015/review_queue.json)。

剩余分层尾部代价候选已在隔离副本实现，默认关闭，仅三个 DieRoute 文件变化。
三层反例在启用后选择 384 代价支路；2,400 个三/四层随机图、7,200 次截断对照、
独立前向单调分层路径代价 oracle、16 项 membership alias 检查及 ASAN/UBSAN
均通过。默认关闭的 20 次主机运行与父版本 350 项产物一致；第一次检查因旧比较器
误删父版本已有 JSON 字段而失败，已留档，修正比较器后重测通过。
同 placement/完整图/原生代价、30 轮上限的三层 pilot 已启动，尚无原生质量改善
或采用结论。见 [候选准备审计](work/rr_remaining_layer_tail_variant_20261015/host_readiness_audit.json)
和 [运行状态](work/rr_remaining_layer_tail_variant_20261015/manifest.json)。

中间层 corridor 诊断新增冻结库三层反例：最后一跳使用精确尾部代价，而较早
入口只看几何，分层算法选择代价 2,496 的支路，flat 选择 384，未触发 fallback。
代价用独立整数算式核对；这证明启发式可错过便宜支路，尚不证明真实 ex5p
超用失败的因果。候选现已按 (RR node, die-path stage) 反向计算剩余
分层尾部代价，保留原 owner/容量/版本语义及默认关闭控制；已开始 pilot，尚未采用。
见 [反例](work/rr_multihop_tail_counterexample_20261015/audit.json) 和
[候选设计](work/rr_multihop_tail_counterexample_20261015/next_variant_design.json)。

三层匹配 pilot 的分层臂已在原定 30 轮上限结束，CPU legal=false，fallback=0；
全部 1,920 条连接有路径、最终树和 occupancy 重计一致，但中间层仍有
15 个超用通道（8 CHANX、7 CHANY），涉及 58 个 net，不能送作合法 QoR 结果。
flat 臂九轮原生合法但 WL/CPD 均退化，因此该 pilot 尚无通过联合门槛的配置。
十二次矩阵队列已按上游失败条件停止，未启动新路由或增加轮数。
完整 30 轮版本/代价回放已通过，最终资源与代价字节一致，失败明确为容量未收敛；见
[失败诊断](work/sb_three_layer_pilot_failure_review_20261015/independent_audit.json)。

常量 zero 硬件候选已配置链接后只读报告队列，等待原链接成功并核验其归档
DCP/xclbin 哈希后，复制指定 routed checkpoint，生成时序、资源、路由、
DRC、约束覆盖、全部时钟/三 CU 时钟和 bus-skew 报告，保留 NA 约束。
目前队列在等待，不是时序通过或最终 bitstream 对应关系证明；指定 routed
checkpoint 可能早于后续 physopt/频率调整，需要单独解释。见
[只读报告队列](work/const_zero_postlink_readonly_reports_20261015/manifest.json)。

冻结 Release 库补充通过三/四层随机图回归：2,400 个固定种子小图上，
upstream、downstream 及两者同时截断共 7,200 次对照，候选 attachment/path、
提交状态与资源字节均与完整搜索一致，搜索展开数未增加。独立 BFS 核对
1,194 个可达及 1,206 个不可达结果，并检查成功路径邻接和终点；64 跳上限
覆盖全部简单路径。这支持观察到的小图截断行为，不证明全局最优、任意输入
等价、原生 QoR 或硬件行为。见
[多层截断审计](work/rr_multilayer_bound_equivalence_20261015/audit.json)。

六组模型的匹配算法矩阵原已冻结并排队，现因 pilot 失败停止：2/3/4 层 × 80/96 通道宽度，每组 fresh
flat/downstream_bounded 各一次，共十二次。队列等待三层 pilot 的实际终态及
独立审计成功才启动，并在协议/输入哈希漂移或检查失败时停止；不自动放宽门槛。
当前只完成准备和排队、已按条件停止，尚无矩阵结果，也不是五次确定性重复、固定总面积或
板上扩展性实验。见 [矩阵协议](work/sb_matched_layer_capacity_matrix_20261015/protocol.json)
和 [队列状态](work/sb_matched_layer_capacity_matrix_20261015/queue.json)。

六组原生树现已完成逐连接层路径核验：三层/cw80 的 1,920 条连接中，
433 条跨两层；四层/cw80 中 151 条跨三层。对应按 net 去重的跨层树边为
999 和 1,266 条；六组均观察到最少相邻层跳数、无层间折返。连接路径计数与
共享树边计数分别保留，均非物理 SLL 流量。见
[多跳路径审计](work/sb_native_layer_path_profiles_20261015/audit.json)。

三层 switchblock 的首个匹配重路由 pilot 已执行至终态：固定 layers3/cw80 的完整
RR 图、placement、原生 indexed cost、30 轮上限及至少三轮在线 STA，比较
flat 与 downstream_bounded，各一次。运行协议、输入/工具哈希与启动脚本
分别冻结；串行执行资源/版本回放、树状态、时序会话来源及原生 VPR 校验。
这仍是可行性 pilot，不是五次重复、规模扩展或质量通过结论。见
[匹配 pilot 协议](work/sb_three_layer_matched_pilot_20261015/protocol.json) 和
[实时执行记录](work/sb_three_layer_matched_pilot_20261015/manifest.json)。

首个 flat 臂已完成九轮，资源/版本回放、树状态及在线时序会话来源审计通过，
并通过 VPR 原生合法性检查。WL=12,075、CPD=10.7603 ns，相对该模型原生
基线 11,615 / 10.4531 ns 分别增加 3.96% / 2.94%；按 net 去重跨层树边
999→931，联合质量门槛失败。downstream_bounded 臂已达到 30 轮上限且不合法；这不是
两臂完整结果或重复实验结论，见
[阶段结果](work/sb_three_layer_matched_pilot_20261015/partial_result.json)。

六组 switchblock 模型已通过完整图打包与原生无算法改动回写预检：累计保留
2,441,074 个节点记录、3,747,204 条有向边（含无连接记录），逐项核对 CSR、
层号、容量、几何和局部延迟；原始树 parent/child、switch、sink pin 身份一致，
各自原生 WL/CPD 不变。随后六组输入均已完成原生 indexed cost 重基，独立核对
全部节点代价映射和全部边基础代价字段；其余字段保持不变。echo 打印精度与
整数皮秒舍入限制仍在；匹配 DieRoute 重路由、质量和扩展性对照仍待完成。见
[原生代价重基审计](work/sb_native_indexed_costs_20261015/independent_audit.json)、
[完整图与原生回写审计](work/sb_native_roundtrip_preflight_20261015/independent_audit.json)。

多层基线扩展发现 OPIN-only 模型的三层方向环存在结构性不可达：对原生失败
连接做完整 RR 图无界 BFS，源只能到达层 2/0，无法到达层 1 目标。
独立的上游跨层 switchblock 模型已通过三层 VPR FULL 路由检查，导出
336,312 个真实 RR 节点；新的 2/3/4 层 × 80/96 通道宽度六组原生基线均已完成
FULL 电路路由和独立元数据/哈希审计。导出节点数为 133,800–773,272，无连接
预分配节点单列（0–341,256），不当作可用物理资源。部分配置保留 missing-fanin
诊断，未证明所有架构引脚或异构工作负载均有效。匹配 DieRoute 对照仍待完成。
固定每层 13×10、电路 ex5p 和种子 1，总面积随层数增长；这不是旧质量基线的
替换、DieRoute 扩展性结果或商业板卡证据。见
[不可达审计](work/native_layer_capacity_scaling_v2_20261015/structural_unreachability_independent_audit.json)、
[三层 switchblock 探测](work/native_sb_three_layer_feasibility_20261015/result.json)。

扇出排序与固定拥塞调度的四组、每组五次原生交互实验已完成。零首轮控制
为 WL=9512、CPD=9.54931 ns；加入扇出排序为 9622、9.65646 ns，模型跨层边
454→446。独立重计跨层边、确定性及 545 项父实验产物记录核验通过，但组合
候选 CPD 超过强基线门槛，不采用。见 [完整交互审计](work/rr_fanout_present_interaction_variant_v2_20261015/independent_audit.json)。

归档硬件 checkpoint 的 bus-skew 专项报告已独立核验：230 条约束中，
229 条数值结果均满足要求，最小裕量 1.490 ns；第 163 条为 NA（1 个 endpoint，
未找到 bus-skew path），未静默豁免。这不改变 setup 失败、约束覆盖及最终映像
对应关系仍未闭合的结论，见 [专项审计](work/archived_sharded_bus_skew_audit_20261015/independent_audit.json)。

固定扇出串行调度的树 seed 权重对照已完成十次原生运行和独立核验。
权重 128 为 WL=9420、CPD=9.74681 ns；权重 256 为 10064、9.78266 ns。
两组各五次确定性检查及 205 项控制组产物匹配通过，但联合质量门槛均失败，
不采用完整权重候选。见 [完整审计](work/rr_fanout_seed_weight_variant_v3_20261015/independent_audit.json)。

扇出排序与 bulk/serial 调度的四组、每组五次原生实验已完成。
扇出 bulk 得到 WL=9996、CPD=9.75744 ns；扇出 serial 为
9420、9.74681 ns。后者改善对应 legacy serial 的两个指标，但仍未通过
强基线 CPD≤9.60037 ns 的联合门槛，故不采用。四组均通过原生合法性；
[终态证据核验](work/rr_fanout_net_order_variant_20261015/terminal_evidence_review.json)
核对结果引用的 85 项小型证据哈希。

读取值观测开关的十次原生运行也已完成，两组均为 WL=9929、CPD=9.63263 ns；
[终态证据核验](work/rr_read_observation_variant_20261015/terminal_evidence_review.json)
核对 55 项证据哈希。该结果支持已记录 journal 的值和 stale/replay 校验，
不证明全部内存访问均被记录；独立 API 访问覆盖实验已由队列启动，仍在执行。

常量起点 zero 检查的隔离硬件候选通过 49,152 项真值检查与 75 次提交差分测试，
已按原 300 MHz 配置成功完成 v++ 编译。29 参数、17 指针、6 AXI master
接口保持一致；HLS LUT 估计从 144002 降到 138809，FF 从 114224 增到
121713，估计周期从 2.433 ns 变为 2.456 ns。尚无布线时序改善结论，见
[HLS 对照](work/native_commit_const_zero_variant_20261015/hls_comparison.json)。

固定零首轮拥塞配置的三个开发案例已完成五次重复、原生合法性、状态回放、
篡改检查及源码绑定时序工具兼容性验证。ex5p 通过模型质量检查，但 diffeq
线长增加 1.17%，alu4 CPD 增加 0.024%，因此联合质量门槛失败，不采用为通用
配置；保留集未打开。完整结果见
[`开发集结果`](work/rr_present_schedule_development_cohort_v1_20261015/result.json)。

独立 criticality shift 对照也已完成十次真实 ex5p 运行和完整审计：clamp 控制
保持 WL=9512、CPD=9.54931 ns，shift 为 9749、9.68003 ns，联合门槛失败，
不采用。跨层边降至 448 不抵消线长/时序退化。见
[`shift 结论`](work/rr_criticality_shift_variant_20261015/interpretation.json)。

持久化 VPR 时序接口已完成真实在线路由验证：22 轮回调及 66 项产物与冻结
对照一致（仅排除 JSON 耗时字段），故障传播和比较器负面检查通过。同一
二进制下的五组交替 CPU 耗时配对已完成并独立核对 660 项产物：独立进程与
持久化模式的中位数分别为 232.42/63.18 秒，配对比值中位数 3.73。包含启动
和关闭开销；共享主机并非隔离性能环境，结果不代表 FPGA 板上加速。

静态任务执行位置对照已完成真实 ex5p 十五次运行、原生检查、任务轨迹及完整
控制器资源/版本重放。三种模式的 41 项核心产物一致，WL=9929、CPD=9.63263 ns，
均未达到强基线质量门槛。目的 die 视图每次涉及 4,444 次任务移动，按日志公式
计 1,476,644 字节；被分类为远端的 shadow 读取项从 16,909,117 降至 1,317,058
（−92.21%）。这些是 CPU observer 和逻辑日志计数，尚非物理网络流量或性能收益。
见 [`静态执行位置完整结果`](work/rr_task_migration_variant_20261015/result.json)。
编码 Task/seed 传输的十五次原生实验及后续回放均已完成，终态审计核对
1,317 个引用文件哈希，并重做父实验语义比较。每个模式一次原生 VPR 检查，
其余重复通过产物匹配核验；三个模式均为 WL=9929、CPD=9.63263 ns，联合
质量门槛失败。见 [终态核验](work/rr_task_transfer_variant_20261015/terminal_evidence_review.json)。
后续额度队列与 seed 独立核验已完成下述完整 ex5p 对照。自适应迁移的完整图验收、speculative read-set
独立重建及硬件执行仍待完成。

新的隔离队列实现将每个 die 的消息槽位与编码字节额度保留至实际搜索完成，
额度不足时等待已有搜索释放；权威提交顺序保持一致。持久序列号拒绝回绕，
取消只允许尚未执行的消息，旧完成/取消票据不能影响后续重发任务。组件与
ASan/UBSan 检查通过；35 次实际小图主机运行通过独立额度和资源/版本重放、
1,225 项产物比较及六种篡改轨迹检查。完整 ex5p 的无额度控制、单槽位限制和
2,076 字节限制三个配置各五次均已完成。额度仅覆盖编码载荷，不代表进程
总内存或硬件带宽界限；见
[`队列实现与验收范围`](work/rr_task_credit_queue_variant_20261015/implementation_progress.json)。
每次单槽位运行处理 11,264 次传输、发生 3,093 次背压；字节限制每次发生
265 次背压。全部重复确定性检查、资源/版本、额度、树结构、时序来源及原生
验收通过，结束时额度均释放。所有配置仍为 WL=9929、CPD=9.63263 ns，未达到
强基线质量门槛。见 [`额度队列完整审计`](work/rr_task_credit_queue_variant_20261015/independent_audit.json)。

接收端 seed 观测副本进一步记录实际传入 RRBackend 的每个节点、跳数和代价。
独立重放器从原始 CSR、已提交树和 STA 输出重建完整 seed 集合，包括未被
最终路径使用的 seed。35 次小图主机运行及 1,225 项对照通过，八种 seed 篡改
被拒绝；三个不可达任务的 seed 也逐项核验，失败后的额度均被释放。
五次完整 ex5p 观测已完成。完整 speculative read-set 重建仍待完成；
见 [`接收端 seed 核验范围`](work/rr_task_seed_observation_variant_20261015/implementation_progress.json)。
每次独立核验 10 个 epoch、11,264 次任务请求的 303,275 条接收 seed 记录；
五次合计 1,516,375 条，资源/版本、额度、树结构、时序来源、静态对照与原生
验收通过。质量保持上述静态结果，联合门槛仍失败。证据见
[`接收 seed 完整审计`](work/rr_task_seed_observation_variant_20261015/independent_audit.json)。

自适应执行位置模式 3 已实现：在 source/sink die 间按冻结公式综合关键度、
边界占用/历史拥塞与在途队列负载进行选择。组件、全部 Q16 关键度阈值、
ASan/UBSan、35 次原模式兼容性与十次自适应主机测试通过。独立重放同时
核验每个 worker 窗口的权威拥塞输入、评分、额度及 seed；八种决策篡改被拒绝，
其中包括保持评分自洽的假拥塞值。静态与自适应各五次的完整 ex5p 实验及
独立审计均已完成；原生质量未达到强基线门槛，硬件流量与性能收益尚待验证。见
[`自适应实现与验收范围`](work/rr_adaptive_task_migration_variant_20261015/implementation_progress.json)。
每次完整 ex5p 自适应运行均通过 5,707 个 worker 窗口、11,264 次决策的权威
拥塞、评分、额度、seed 与状态重放。背压事件为 2,025 次，静态目的 die 控制
为 3,093 次（−34.53%）；远端分类读取则从 1,317,058 增至 5,124,816 项
（+289.11%）。所有重复确定性检查和原生验收通过，WL=9929、CPD=9.63263 ns
保持一致，联合质量门槛仍失败。这些是软件计数上的取舍，尚不能推出硬件
延迟或流量收益。见 [`完整自适应对照审计`](work/rr_adaptive_task_migration_variant_20261015/independent_audit.json)。

读取值观测副本按明确的 64 字节小端记录，输出每个初次资源读取实际看到的
容量、占用、owner、版本和宽代价，并区分初次搜索与过期后的权威重放。
二十次主机测试通过独立窗口快照/shadow/owner 混合值、日志计数/哈希与过期判断
重建，750 项对照一致，十一种损坏记录被拒绝。三个不可达搜索产生五条读取
记录和两次过期重放，均已核验；ASan/UBSan 通过。固定三个窗口发布一次的
完整 ex5p 观测关闭/开启各五次均已完成，终态证据核验通过。验证范围是实际记录的读取日志；
完整搜索访问集合的独立枚举和硬件一致性仍待完成。见
[`读取值观测与验收范围`](work/rr_read_observation_variant_20261015/implementation_progress.json)。
首个完整 ex5p 观测已完成 49,069,223 条读取值的独立重放，包含 5,122,213 条
远端 shadow 记录和 2,686 次过期/权威重放；与实际路由计数完全对应。
3,140,430,272 字节的记录按流处理，同一二进制关闭观测的核心产物对照通过；
后续重复和最终原生验收也已完成，两组质量均为 WL=9929、CPD=9.63263 ns，
未通过联合门槛。见
[`完整读取值终态核验`](work/rr_read_observation_variant_20261015/terminal_evidence_review.json)。

另一个隔离副本在 `RRStateView.resource/cost` 接口处维护独立的节点访问统计，
与 `ResourceReader` journal 的节点集合逐项对应，并检查逐节点及全局调用次数。
审计开启时拒绝 `borrowed_data()` 裸指针出口；调用次数包含读取值观测的额外
代价查询。二十次实际主机测试、770 项对照（含读取值二进制文件）、十一种
读取值和九种访问统计损坏检查通过，ASan/UBSan 与失败搜索检查通过。
完整图开关对照十次运行及终态独立审计均已完成。每次覆盖候选中，13,950 个 proposal 阶段、
49,069,223 次唯一节点出现与 journal 精确匹配；资源/代价 API 调用分别为
269,360,030/248,635,515 次，后者包含诊断快照查询。五次覆盖共 245,346,115 次唯一节点出现，235 项控制产物匹配；当前
1,019 个文件、约 43.38 GB 证据已流式校验。两组质量均为 9929/9.63263，
未通过联合门槛。见
[`完整原生覆盖审计`](work/rr_view_access_coverage_variant_20261015/independent_audit.json)。
这验证显式接口调用覆盖，尚非任意 C++ 指针访问的形式化证明或硬件一致性结论。见
[`双重访问统计与验收范围`](work/rr_view_access_coverage_variant_20261015/implementation_progress.json)。

原生 VPR 的路由前关键度观测已通过五次 canonical 兼容性检查，并与全部 1,920
个 ex5p 逻辑 pin/task 精确对应。量化初始值为 42,123–64,880（22 种），现有输入
则统一为 32,768。仅替换初始关键度的五组交替对照及独立审计已完成，后续 STA
clamp 保持一致。候选 WL=9665、CPD=9.69023 ns，均差于强基线 9664/9.60037 ns，
因此不采用。原 uniform 控制通过 330 项产物对照并保持 9512/9.54931 ns。见
[`初始值映射`](work/ex5p_native_initial_task_join_20261015/audit.json)与
[`实验结论`](work/rr_native_initial_criticality_study_20261015/interpretation.json)。

新的质量诊断固定比较两项调度因素：原有 net 顺序与 sink 数降序，以及批次
连接处理与串行整网处理，共四个配置、各五次完整 ex5p 运行，现已启动。
原生 VPR 的调度源码提供了 sink 数降序的依据；新实现保持输入 Task 的
priority 字段及其他代价/时序参数。批次配置只改变分批成员，批次内仍按原
priority 执行；串行配置每次一个任务，才对应实际整网 fanout 顺序。二十次
主机测试、340 项旧控制对照、完整 dispatch/状态重放和六种篡改检查通过；
ASan/UBSan 明确使用消毒器二进制验证了两个新模式。此项属于复用基线策略
的校准，不代表新的 DieRoute 算法或已通过质量门槛。见
[`fanout 调度实验`](work/rr_fanout_net_order_variant_20261015/implementation_progress.json)。

分 bank 硬件已完成链接，独立读取归档 checkpoint 确认 300 MHz setup 失败：
WNS=-2.014 ns、TNS=-22733.928 ns。最终映像报告 achieved/DATA 187 MHz，
尚无调整后频率的独立签核。最终 bitstream 对应关系、完整时序/约束签核和
板上运行仍未完成。见
[`独立报告审计`](work/native_snapshot_sharded_independent_report_audit_20261015/audit.json)。

## 当前实现与边界

- `src/dieroute.cpp` 是早期单边界 greedy 原型，队列字段只有统计；其
  `shadow_updates` 计数不构成完整 shadow coherence，也没有实际 HBM bank 映射。
- `src/corridor.cpp` 是新增 C++ 多跳预留参考实现：确定性最小代价简单 die
  路径、全部 hop 验证后原子提交、按权威 reservation slot 释放、版本冲突检测、
  generation 防止旧请求释放复用后的 slot。代价包含容量压力、history 和
  criticality-weighted delay。调用方负责固定任务顺序、冲突后的重新规划和
  die 内路由失败后的释放。版本耗尽时明确拒绝，不允许 wraparound。
- 当前 `Boundary` 每项必须描述独立的可预留容量池。该协议尚未连接真实 RR
  router；不能把 cross-layer RR edges 当作相互独立的物理 SLL。
- `src/rr_backend.cpp` 已通过 PR 的 `KernelBatchExecutor` 接入完整控制闭环。
  它对实际跨 die 边的两端 RR ID 建立去重的候选预留日志，再进行 die 内搜索、
  失败撤销、替换出口和有计数的全图回退。共享路由树、rip-up、拥塞迭代由
  PR 维护；原有 `Boundary` 聚合容量接口没有被不安全地套用到真实 RR 边上。
  默认是串行 C++ golden executor。可选 `SpeculativeBackend` 已接入并发只读
  搜索、完整版本日志验证与边界摘要 shadow；仍没有硬件 shadow 网络。
  negotiated-congestion 轮次允许中间超用并单独计数，最终必须满足原生容量。
- PR 的普通 C++ PathFinder 可直接消费原生多层 VPR 图，完成路由树回写和
  VPR 原生检查。这是无 DieRoute 分区的对照，并非 DieRoute 新算法结果。

## 开发验证

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build -j4
ctest --test-dir build --output-on-failure
```

`corridor_tb` 检查多跳、最后一跳冲突的无副作用、释放与其他预留交错、重复/旧
释放请求、版本与容量溢出，并在 2,000 组固定种子随机拓扑上与穷举路径比较。
转换器检查显式 layer、连续 ID 和重复写入拒绝。旧 `run_hls.tcl` 仍只覆盖旧
`dieroute_kernel`；corridor/完整路由协议尚无 HLS/RTL 证据；摘要端点的独立验证见文末。

`rr_backend_tb` 进一步覆盖三 die 路由、同 net 多 sink 共享、不同门户对同一 RR
资源的容量别名、局部搜索失败后的预留撤销、跨 die 后重返原 die 的全图回退、
两 net 容量竞争和提交前溢出拒绝。新增测试覆盖下游延迟/拥塞改变出口选择、
已有入口与新入口的比较，以及 1,000 组随机图上的有界/完整反向搜索等价性。
九项 CTest、RR 后端/宽代价/投机执行层 ASan/UBSan，以及投机执行层
ThreadSanitizer 已通过。

## 原生双 die 输入与 PR 对照

`tools/run_native_case.py` 在新目录运行 VPR，并保留命令、退出状态、日志和
输入/产物 SHA-256。使用 VTR 自带的
`arch/multi_die/stratixiv_3d/3d_full_OPIN_inter_die_stratixiv_arch.timing.xml`，
`--device auto` 保留架构原有双层定义；不把二维图按 XY 人为贴标签。

```bash
python3 tools/run_native_case.py --vpr /path/to/vpr \
  --arch /path/to/3d_full_OPIN_inter_die_stratixiv_arch.timing.xml \
  --circuit /path/to/circuit.blif --device auto --channel-width 80 \
  --output work/new_native_case
python3 tools/run_pr_reference.py work/new_native_case work/new_pr_reference
```

第二步冻结并编译 PR 源码，导出连接，打包 production ABI，生成逐 RR node 的
little-endian u16 `.node_die` sidecar，执行至少五次 PR 路由，并回写 `.route`
交原生 VPR 检查。输入从相同 placement 和 RR graph 派生。当前对照使用固定
criticality=32768、base cost=64；尚未启用逐轮 STA，不能冒充完整 timing-mode
或 HBM C-model 基线。Python 只做转换、运行编排和统计，路由由 C++ 执行。

2026-10-13 初始结果（均为软件功能/基线证据）：

| 案例 | RR nodes / edges | connections / 跨 die 端点 | PR 原生合法 | 五次哈希一致 | PR 相对 VPR WL / CPD |
|---|---:|---:|---|---|---:|
| rca_5bit | 14,060 / 46,462 | 17 / 5 | 是 | 是 | -0.85% / 0.00% |
| diffeq（4-LUT 输入） | 69,848 / 392,336 | 2,073 / 506 | 是 | 是 | +5.26% / +0.54% |

`diffeq` 的 WL 不劣门槛尚未通过。这些案例采用可信的公开 VTR 架构模型，
不代表商业 UltraScale+ SLL 或板上性能，也不足以覆盖正式 benchmark 主表。

## 完整 RR 分层闭环的首轮结果

```bash
python3 tools/run_rr_pair.py work/new_native_case work/new_pr_reference work/new_pair
```

实验器冻结当前 DieRoute/PR 源码并重新编译，在同一 PR 控制层下比较 `flat`
与 `hierarchical`，各运行五次，保存逐轮哈希并分别回写交 VPR 检查。所有测量
是 CPU 参考模型时间。`flat` 的 wave 调度与上表普通 PR 的逐 net 调度不同，
不能混用两个对照。当前参数属于 `diffeq` 开发集探索，尚未冻结为测试集配置。

| diffeq 版本 | 模式 | 原生合法 / 五次一致 | 迭代 | 扩展节点数 | 原生 WL | 原生 CPD (ns) |
|---|---|---|---:|---:|---:|---:|
| v1 | flat | 是 / 是 | 3 | 7,349,510 | 9,285 | 7.66331 |
| v1 | 几何出口选择 | 是 / 是 | 4 | 31,141,492 | 9,791 | 7.80484 |
| v2 | flat | 是 / 是 | 3 | 7,349,510 | 9,285 | 7.66331 |
| v2 | 排除不可达出口 | 是 / 是 | 13 | 3,899,951 | 9,965 | 7.88315 |

VPR 基线 WL=8,639、CPD=7.61372 ns。v2 分层路由相对 VPR 的 WL/CPD 分别
为 **+15.35%/+3.54%**，因此 QoR 验收仍失败，不能宣称已达研究目标。
v1 的 1,159 次出口修复来自大量不可达候选；v2 通过完整 RR 入边的唯一前驱
链证明出口属于其他 SOURCE 后排除它们，不对有多个前驱或环的节点作此推断。
v2 在该案例中没有局部失败或全图回退，但仅按几何/边界代价选择出口仍未
反映下游路由代价和拥塞，不能据零回退断言方案更优。
后续定点回溯审计还确认此 13 轮 v2 运行发生了拥塞系数饱和，不能作为
合格的定点质量/性能证据；保留数值仅用于失败诊断。

原始冻结实验：`work/rr_pair_diffeq_v{1,2}_20261013/pair.json`。其中
`committed_crossings` 是所有迭代累计的提交事件数，不是最终物理 SLL 使用量。

## 下游代价、共享树入口比较与时序反馈

`downstream` 模式用当前资源快照上的 die 内反向搜索评估最后一个出口的
下游代价；前端仍采用几何估计，因此不是全局最优路由证明。若共享树已经
进入目标 die，同时比较沿用入口和新建 corridor 的完整增量路径代价，全部
候选只在胜出后提交。额外反向搜索、未采用的候选和失败尝试均计入统计。

三个开发案例采用相同参数、原生双层架构和五次重复：

| 案例 | flat 相对 VPR WL / CPD | downstream v2 相对 VPR WL / CPD | 最终跨层边：VPR / flat / downstream |
|---|---:|---:|---:|
| diffeq | +7.48% / +0.65% | +7.21% / +0.63% | 345 / 323 / 330 |
| alu4 | -0.66% / +9.24% | -1.36% / +8.97% | 377 / 316 / 317 |
| ex5p | +5.96% / +17.12% | +4.80% / +14.92% | 484 / 409 / 405 |

所有结果原生合法、路径和语义计数五次一致，但没有案例同时通过相对 VPR
的 WL/CPD 不劣门槛。这里按每个 net 的唯一跨层树边计数，不是商业物理 SLL
数量。原生 trace 的 leaf 到下一个 branch anchor 不计作边，计数器有独立测试。

`downstream_bounded` 使用非负入口代价和已找到的完整候选作为停止界限；
只有反向队列的最小代价严格超过该界限才停止，保留相等代价的 tie-break。
`diffeq` 上与完整 downstream v2 的路径、资源、迭代和审计 CSV 逐字节一致，
反向扩展从 **11,483,438** 降至 **2,783,701**（-75.76%），含全部局部搜索的
总扩展从 14,868,495 降至 6,168,758。这是算法工作量证据，尚无 HBM/板上加速结论。

```bash
python3 tools/run_rr_pair.py work/new_native_case work/new_pr_reference work/new_pair \
  --modes downstream downstream_bounded
```

完整开发证据和交叉边审计见
[`experiments/downstream_crossing_audit_20261013.json`](experiments/downstream_crossing_audit_20261013.json)。
开发/保留验证集边界见 [`experiments/cohort_protocol_v1.json`](experiments/cohort_protocol_v1.json)；
保留集尚未打开，不把已用于选择算法的三个案例称为 held-out 结果。

可选 `--timing-vpr /path/to/patched/vpr` 启用 PR 的逐轮 Tatum adapter，至少执行
三轮，每轮更新 criticality。它对 additive RR delay 做 STA 反馈，最终 QoR
仍以原生回写为准。`diffeq` 首轮五重复的结果如下：

| 时序模式 | 迭代 | WL | CPD (ns) | 相对 VPR WL / CPD |
|---|---:|---:|---:|---:|
| flat | 3 | 9,344 | 7.63363 | +8.16% / +0.26% |
| downstream v2 | 6 | 9,618 | 7.63336 | +11.33% / +0.26% |

证据见 [`experiments/timing_feedback_audit_20261013.json`](experiments/timing_feedback_audit_20261013.json)。
时序改善伴随线长变差；当前不是可接受的联合 QoR 解。

### 共享树上游延迟消融

`--tree-timing-weight-q 256` 将已有树路径的 criticality-weighted delay 完整
计入搜索 seed（Q8；默认仍为 0）。该值通过 host 的
`DIEROUTE_TREE_TIMING_WEIGHT_Q` 传递，并写入每次结果和冻结实验配置；超过
u16 或负数会拒绝。审计会核对实际执行值与声明值，避免未记录的环境参数。

定向测试发现并修复了一个不一致：详细搜索使用 seed cost，但出口预选曾
忽略它。预选现按 `seed cost + geometry estimate` 比较；它仍是估计，不能
声称得到全局最优路径。完整 PR 控制层测试验证高关键度第二个 sink 会避开
慢共享入口，零关键度时保持原选择；随机等价性测试也覆盖不同代价的多个
seed 和已有目标 die 入口。

三个开发案例使用固定权重 256、固定关键度，完整/有界下游搜索各重复五次：

| 案例 | WL | CPD (ns) | 相对 VPR WL / CPD | 完整 / 有界总扩展节点数 |
|---|---:|---:|---:|---:|
| diffeq | 9,581 | 7.66154 | +10.90% / +0.63% | 15,350,423 / 6,768,683 |
| alu4 | 8,164 | 9.85513 | +5.57% / +3.81% | 14,305,193 / 8,804,702 |
| ex5p | 10,765 | 10.4412 | +11.39% / +8.76% | 17,416,573 / 10,559,214 |

全部原生合法、重复确定，完整/有界输出逐字节一致。上游权重改善了部分
案例的 CPD，但线长增加，仍无联合 QoR 通过案例，因此不改默认权重。
出口预选修复在定向案例中改变选择，在以上三个真实开发输入上不改变
最终语义输出。修复前后证据分别见
[`tree_timing_v1_audit_20261013.json`](experiments/tree_timing_v1_audit_20261013.json) 和
[`tree_timing_v2_audit_20261013.json`](experiments/tree_timing_v2_audit_20261013.json)。

权重 256 加逐轮 Tatum 反馈的 `diffeq` 对照也各完成五次：flat 为
WL=9,772、CPD=7.63363 ns，downstream_bounded 为 WL=9,525、CPD=7.63431 ns，
均三轮收敛。后者相对 VPR 为 **+10.26%/+0.27%**；比匹配 flat 更短不代表
通过原生 VPR 门槛。见
[`tree_timing_feedback_v1_audit_20261013.json`](experiments/tree_timing_feedback_v1_audit_20261013.json)。
出口预选修复后的时序模式也完成五次，语义输出与修复前一致，见
[`tree_timing_feedback_v2_audit_20261013.json`](experiments/tree_timing_feedback_v2_audit_20261013.json)。

### 原生基础代价与拥塞/关键度目标

原生 VPR 日志使用 `DELAY_NORMALIZED_LENGTH`，原 PR 输入却给所有边相同的
base=64。`tools/native_base_costs.py export` 在相同冻结 RR graph 和原生合法
route 上运行 VPR analysis，导出 `rr_indexed_data.echo`，按真实 node type 和
segment ID 映射基础代价。以 diffeq 为例，L4/L16 分别约为 95/380 ps，
SOURCE/OPIN/IPIN/SINK 分别为 24/24/23/0 ps。转换只替换 edge 的基础代价，
保持图、延迟、任务、资源不变；未知映射、负值、非有限值、u16 溢出均拒绝。
原生 echo 有打印精度限制，输出还进行了整数 ps 舍入，不能声称位精确复现 VPR。

```bash
python3 tools/native_base_costs.py export work/new_native_case work/new_native_costs
python3 tools/run_rr_pair.py work/new_native_case work/new_pr_reference work/new_pair \
  --modes flat downstream downstream_bounded --native-base-costs work/new_native_costs
```

另一个独立开关 `--cost-model vpr_style` 将 PR 的 Q8 历史/当前拥塞字段解释为
乘数，使用 `B*(1+H/256)*(1+P*overuse/256)` 后按 `(1-criticality)` 加权，再加
criticality-weighted delay。整数实现分别对拥塞项和延迟项取下整，累积代价
溢出时拒绝，不回绕。host 对初始任务和每次 STA 返回值统一使用约 0.99 的
criticality 上限（64880/65535），随后 PR 基于同一值生成上游 seed cost。
默认仍为原 additive 形式。此选项不是完整 VPR 克隆：fanout 缩放、RC 路径
依赖、不可配置资源集合和控制层参数仍有差异。

固定关键度、树权重 0 的三个开发案例，downstream_bounded 结果如下：

| 案例 | 仅原生基础代价：WL / CPD 相对 VPR | 再启用 vpr_style：WL / CPD 相对 VPR | vpr_style 定点有效 |
|---|---:|---:|---|
| diffeq | +5.90% / +0.63% | -0.13% / +0.63% | 是 |
| alu4 | -3.05% / +10.32% | -7.10% / +10.39% | 是 |
| ex5p | +1.21% / +18.21% | -1.42% / +13.96% | **否：14 轮中发生饱和** |

各模式原生合法，五次语义确定；完整/有界下游搜索输出一致，但均未通过联合
QoR 门槛。ex5p 的 vpr_style 数值仅供失败诊断，不进入有效主表。证据见
[`native_base_cost_audit_20261013.json`](experiments/native_base_cost_audit_20261013.json) 和
[`vpr_style_cost_audit_20261013.json`](experiments/vpr_style_cost_audit_20261013.json)。

PR 的拥塞控制字段仍为 u16，默认倍增在第 9 轮开始饱和。当前 host 在 epoch
首次执行前检查 present/history=65535 并中止；旧实验的审计则明确标记
`fixed_point_valid=false`、`quality_evidence_eligible=false`。不能通过继续使用
饱和值或放宽验收来宣称收敛。新的 ex5p 重放已验证中止行为；未饱和 diffeq
在加检查前后的六类语义产物完全一致。

权重 256 加 STA 的新 vpr_style diffeq 实验也在已完成重复中出现 15 轮饱和，
因此中止剩余重复并保留 `work/rr_pair_diffeq_timing_vprcost_v1_20261013/termination.json`。
它没有完成五次/原生回写验证，不是有效时序实验。扩位后的重跑见下节。
全部旧 paired 实验的回溯标记见
[`fixed_point_retrospective_20261013.json`](experiments/fixed_point_retrospective_20261013.json)。

### 64 位拥塞代价与控制层重放

`--cost-bits 64` 使用 `src/wide_controller.cpp`：它从文件头记录 SHA-256 的
PR accelerated controller 移植当前使用的调度、route tree、rip-up 和 timing
逻辑；上游 PR 文件和旧实验不变。它不是新的路由算法贡献。当前 API 不含
PR 的可选 cleanup；DieRoute 此前的配对实验也没有启用该功能。

拥塞的 present/history 均放入独立 u64 数组；增长、历史更新、资源版本及
总代价溢出都会明确拒绝。代价更新先验证全部节点再提交，最后一个节点的
版本溢出不会留下部分更新。乘法模型使用受界限检查的 128 位中间运算和
商/余数分解；不会先计算并不启用的代价模型而错误触发溢出。

输出 schema 通过 JSON 的 `cost_state_bits`、`resource_encoding` 和
`cost_encoding` 声明：64 位模式的 `.resources` 保留 occupancy/capacity/
version/owner，原两个 u16 cost 字段为零/保留；`.costs` 每节点保存
little-endian `{present:u64, history:u64}`。每轮 `.iterations.csv` 使用完整
u64 系数，`.audit.csv` 的逻辑资源哈希包含真实宽代价。审计器核对二进制、
每轮增长关系、最终逻辑哈希和五次重复，不能只检查 `legal=true`。

```bash
python3 tools/run_rr_pair.py work/new_native_case work/new_pr_reference work/new_pair \
  --modes flat downstream downstream_bounded --native-base-costs work/new_native_costs \
  --cost-model vpr_style --cost-bits 64
```

三个开发案例各模式均完成五次、原生合法、无饱和，完整/有界下游搜索输出
一致。固定关键度、树权重 0 的 downstream_bounded 结果如下：

| 案例 | 迭代 | 最终 present (Q8) | WL | CPD (ns) | 相对 VPR WL / CPD |
|---|---:|---:|---:|---:|---:|
| diffeq | 6 | 8,192 | 8,628 | 7.66154 | -0.13% / +0.63% |
| alu4 | 6 | 8,192 | 7,184 | 10.4801 | -7.10% / +10.39% |
| ex5p | 14 | 2,097,152 | 9,527 | 10.9403 | -1.42% / +13.96% |

见 [`wide_cost_audit_20261013.json`](experiments/wide_cost_audit_20261013.json)。
diffeq/alu4 的路径、逐轮哈希和重构后的资源与旧 16 位版本一致；ex5p 的
前八轮审计一致，第九轮起按真实宽系数更新。扩位消除了无效定点证据，
**没有消除 CPD 退化**，因此仍不满足联合质量门槛。

宽代价下，树权重 256 加逐轮 Tatum 反馈的 diffeq 已各完成五次，原生合法、
代价有效且语义输出一致：flat 15 轮，WL=9,235、CPD=7.60939 ns；
downstream_bounded 7 轮，WL=8,996、CPD=7.61167 ns。后者相对 VPR 为
**WL +4.13%、CPD -0.027%**，仍未通过联合门槛。见
[`wide_timing_diffeq_audit_20261013.json`](experiments/wide_timing_diffeq_audit_20261013.json)。

相同宽代价/时序配置的 alu4 也完成五次原生合法验证：flat 7 轮，WL=8,321；
downstream_bounded 8 轮，WL=8,353；两者 CPD 都为 9.43037 ns。后者相对
VPR 为 **WL +8.02%、CPD -0.67%**，仍未通过联合门槛。见
[`wide_timing_alu4_audit_20261013.json`](experiments/wide_timing_alu4_audit_20261013.json)。

ex5p 的相同配置也完成五次：flat 五次都在 30 轮后剩一个超用资源，明确
报告 routing failure，不提供合法 QoR；downstream_bounded 五次均在 22 轮
原生合法收敛，最终 present=536,870,912，WL=10,762、CPD=9.81893 ns。
后者相对 VPR 为 **WL +11.36%、CPD +2.28%**，仍未通过联合质量门槛。
三个开发案例的完整时序审计见
[`wide_timing_cohort_audit_20261013.json`](experiments/wide_timing_cohort_audit_20261013.json)。
定点有效、重复确定和路由合法是独立条件：flat 的失败不能因没有溢出而
被改记为成功，也不能从 native QoR 表中无说明地删去。

`wide_costs_tb` 覆盖 30 轮重路由、系数超过 u32、共享树/占用、不可解容量
竞争、历史更新在 rip-up 之前发生，以及溢出无副作用。原搜索随机测试还
覆盖宽代价下完整/有界反向搜索等价性。上述是 CPU golden 证据；宽代价
尚未移植到 HLS/HBM 数据面，不能用其 CPU 时间作 FPGA 性能结论。

所有审计由 `tools/audit_rr_experiments.py` 重新核对冻结源码、可执行文件、
输入与输出哈希、重复语义计数和原生日志中的合法性/QoR 字段；不只读取
manifest 的 `passed` 标记。当前开发运行存在并行的其他任务，CPU wall time
只作诊断记录，不作为正式性能统计或 FPGA speedup。

## 商业 SLR 拓扑与路由

商业拓扑检查已在隔离的 RapidWright runtime 中加载原生 `xcu280` 数据库，
确认三个 SLR；上游 PR 数据目录保持只读。`tools/SlrNodeProbe.java` 枚举
原生 `LAG_LAG` 类型的 4,800 个 tile，对相连电气节点按 PR 的 canonical
wire 规则去重，再导出全部成员 wire 及其原生 SLR。该范围包含 2,041,620
个唯一节点、17,847,840 条成员 wire 记录；46,100 个节点具有跨 SLR 归属，
其中 46,080 个为 `NODE_LAGUNA_DATA`，20 个为全局时钟类节点。

`tools/audit_slr_census.py` 已核对原生数据库/产物哈希，并逐节点用 wire 表
重算成员数、SLR 集合和代表 wire 归属，见
[`native_slr_census_audit_20261013.json`](experiments/native_slr_census_audit_20261013.json)。
这直接证明代表 wire 的单一 SLR 字段会丢失跨 SLR 信息；它仍是部分器件
拓扑诊断，不是完整商业 RR 图、独立 SLL 容量证明、DCP 回写或上板结果。
初次按 `LAGUNA` tile 名筛选未命中而拒绝运行的记录也保留；实际数据库
采用 `LAG_LAG` 类型。冻结命令、Java 源码及原始 CSV 位于
`work/slr_node_census_v2_20261013/`。

### 多 SLR 电气节点已接入 C++ 路由闭环

`RRBackend` 可接收两项成对的 native sidecar：`.node_membership` 每个 canonical
电气节点保存一个 little-endian u16 SLR 位掩码（当前最多八个 SLR），
`.edge_die` 按 CSR 边顺序保存每条 PIP 的 native SLR ID。原 `.node_die`
只选择唯一 authoritative owner；所有 SLR 仍共享原节点的一份 occupancy、
capacity、version 和代价。VPR 单层节点表示及已有输入保持兼容。

die 内搜索按 PIP 所在 SLR 限制邻接。一个跨 SLR 电气节点内部的转换不新增
RR 节点、路径项、跳数或占用；它也不凭空添加延迟，真实延迟仍须由输入
代价模型提供。共享树中的节点可以从其任一 SLR 成员继续扩展。对不一致的
PIP/节点归属、超过八个 SLR 的位掩码、缺失配套 sidecar，以及无法从节点
序列唯一还原的平行 native PIP，旧节点路径接口明确拒绝；新增显式边接口见下文。多 SLR source/sink
还需要任务级 pin access 信息，当前同样拒绝，不能靠选择代表 SLR 静默处理。

`NativeSlrGraph.java` 从 U280 原生 `LAG_LAG_X4Y539/UBUMP0` 导出了一个邻域：
七个电气节点、六条 PIP，中心节点同时属于 SLR1/SLR2。
`pack_native_slr_graph.py` 保留原电气节点 ID，核对所有成员 wire 与 PIP
端点后打包。该功能输入明确采用单位 base cost、零延迟和容量一；它不是
商业设计的时序输入。源端按 PR 合约为独占 root，occupancy 统计 route-tree
child 节点。打包器拒绝两个 net 共享 source 或有歧义的源端访问。

四种模式对共享树、反向跨界和双 net 容量竞争分别重复五次，共 60 次。
合法案例原节点容量精确重计数且语义输出确定；竞争案例均保留一个超用
资源并明确失败。独立 Java 回查确认三条路径的六条 PIP 原生存在、电气
连续，并拒绝篡改的端点。另有 1,000 组随机三 SLR 图检查宽代价下完整/
有界反向搜索的等价性。三个 VPR 固定关键度开发案例的七类语义产物和
已有非时间计数与此前冻结结果一致。

证据目录为 `work/native_slr_routing_v3_20261013/` 和
`work/native_membership_verification_20261013/`。这是 native 拓扑与路由协议的
功能证据，尚无 DCP 回写、完整商业 RR 图、真实商业时序、并发 shadow 或
板上结果。`committed_crossings` 仍统计 canonical owner 相邻变化事件，
尤其在多成员节点上不能解释为最终 SLL 数量。最终 SLL 使用必须按原生资源
身份及每个 net 去重另行审计。

### 完整 U280 DCP 输入与未改路由的回写检查

2026-10-13 已检查 PR 完整实现的 `level0_wrapper_routed.dcp`，输入 SHA-256 为
`8a1638cc183eab4050630e3cc070e621c6223b536dcd0b400cc08ed1c9ea2a61`。
这是已有 PR 加速器与平台 shell 的商业器件设计，用于验证转换链；它不是
DieRoute 重路由结果或独立测试集。所有操作使用 DieRoute 工作目录中的副本。

`tools/run_dcp_check.py` 生成 Vivado 原生路由、时序、利用率和默认 DRC 报告，
可显式导出 RapidWright 可读 EDIF。首次直接读 DCP 因内嵌 EDIF 不可读且
自动生成进程找不到 Vivado 而失败；显式导出已解决。加密 IP 的 `.edn` 文件
和 RapidWright 生成的 `*_load.tcl` 必须一同保存，不能仅交付回写 DCP。

`tools/run_dcp_inventory.py` / `DcpSlrProbe.java` 已导出 963,825 个物理 net
记录、2,928,754 个 site pin 和 11,500,192 个 PIP。按实际引脚 SLR，
非时钟、非静态的跨 SLR net 共 15,252 个：SLR0/1 为 9,497 个，SLR1/2
为 5,505 个，SLR0/2 为 230 个，三个 SLR 均有端点的为 20 个。全部跨 SLR
信号均有 source，所有导出引脚均有原生位置，任务端点没有多 SLR 节点歧义。

完整物理检查按 site/BEL 枚举，包含同名 `<LOCKED>` 和 multi-BEL 项；不能
用 `Design.getCells()` 中一个 `<LOCKED>` 代表项的位置作一致性判断。共
857,493 个 cell 记录，其中 857,164 个有 site/BEL，329 个未放置，32,617
个标记为 locked；另有 66,143 个 site。回写前后五类清单逐字节一致：
net/PIP 指纹、物理引脚、cell 放置与标志、cell pin mapping、site 内 PIP
及 wire-to-net 指纹。初版代表项位置不一致的失败检查完整保留。

| Vivado 检查 | 原始 DCP | RapidWright 未改路由回写后 |
|---|---:|---:|
| 完整路由 net / 路由错误 | 640,797 / 0 | 640,797 / 0 |
| WNS / TNS（ns） | +0.016 / 0 | +0.016 / 0 |
| 原生 SLL 使用量 | 15,502 | 15,502 |
| 默认 DRC Error / Critical Warning | 0 / 0 | 0 / 0 |
| 默认 DRC Warning / Advisory | 438 / 5 | 438 / 5 |
| 层次 cell 数 | 831,721 | 831,714 |
| 层次 net 数 | 3,760,858 | 3,760,846 |
| route-status 逻辑 net 数 | 1,061,821 | 1,061,816 |

setup/hold/pulse 的 slack、失败端点及总端点计数、DRC 各规则计数、原语利用率
也一致。但完整原生字段比较仍明确失败，不能只凭物理清单相同宣布完全等价。
`EdifHierarchyProbe.java` 定位到：原始可读 EDIF 与 RW 写回的层次清单相同；
Vivado 再加载后移除了七个 VCC 实例，另有 524 个实例的类型端口数、九个
实例的内部 net 数和七个实例的子实例数变化。下述进一步检查已解释这些
差异在叶子接口上的影响；仍未检查 bus skew、生成 bitstream 或执行 DieRoute
重路由。

原生对照在 `work/u280_dcp_native_comparison_20261013.json`，五类物理清单比较
在 `work/u280_dcp_roundtrip_comparison_v2_20261013/`，层次差异诊断在
`work/u280_edif_hierarchy_audit_v2_20261013/`。完整入口、失败记录和范围见
[`dcp_frontend_progress_20261013.json`](experiments/dcp_frontend_progress_20261013.json)。
G1 仍未完成：还需完整商业 RR 图/代价与任务接入、保留背景资源的实际重路由
及原生 QoR 验证。硬件性能与能耗也仍缺物理 U280；该轮重新核验
PCI 中没有 Xilinx 卡，`xbutil examine` 报告 0 devices。

### 层次别名与叶子端点连接验证

`EdifConnectivityProbe.java` 按 EDIF 端口成员索引展开层次 net，并用并查集
合并边界别名。每个原语或 opaque 叶子的全部声明端口位、顶层端口位均有
记录，包含无 net 的悬空位；常量驱动不作全局合并。对每个连接组，将全部
端点身份排序后计算 SHA-256，同时保留端点数。叶子的实例属性、类型属性、
端口属性及方向另行核对。这里的 Java 只执行输入转换和验证，不执行路由。

完整设计三阶段验证已完成：原始 Vivado 可读 EDIF、RW 写回的内嵌 EDIF、
Vivado 重载后导出的 EDIF。前两个阶段的端点、叶子清单及汇总逐字节一致。
第三阶段保留的 **774,378 个叶子记录和 4,537,715 个端点记录完全一致**；
少了七个 `hdi_primitives/VCC` 实例及其输出端点。逐一验证其原始连接组
只有该输出自身，未连接到其他叶子引脚或顶层端口。另减少五个不含任何
叶子／顶层端点的连接组。全部 183,251 个无 net 的声明端口位均被保留。

审计器仅允许上述无负载常量删除，不能忽略有负载的常量、普通悬空输入或
改变的叶子属性；原生字段的严格相等检查仍保留为失败，未修改计数或日志。
这证明的是原语／opaque 单元边界上的连接保留，不包含加密单元内部形式化
等价证明，也不能代替新路由的合法性、时序或 SLL 延迟验证。

独立的小型 EDIF 夹具给出 21 个端点、12 个连接组的手工预期，覆盖重复层次
实例、纯连线模块、非零起点升／降序总线、双向端口和悬空位。首次测试发现
当前 SDK 的位名辅助函数把 `A[2:3]` 映射为负索引；适配器已改用原始成员
索引解析外部与内部连接，未修改上游 SDK 或测试预期。修正版通过原失败输入
复核；完整 U280 三阶段产物与修复前逐字节一致。改名、删除无负载常量的
正例通过；交换总线连接、删除有负载常量、修改叶子属性、删除声明悬空输入
四类反例均被拒绝。

可复用入口为 `tools/run_edif_connectivity.py` 与
`tools/audit_edif_connectivity.py`。原始产物在
`work/u280_edif_connectivity_v2_20261013/`，最终审计在
`work/u280_edif_connectivity_native_audit_v2_20261013/`，独立测试在
`work/edif_connectivity_fixture_checks_v2_20261013/`。冻结源码、全部产物哈希
与上游只读核对见
[`edif_connectivity_progress_20261013.json`](experiments/edif_connectivity_progress_20261013.json)。

## CPU 并发与边界 shadow

`src/speculative_backend.cpp` 在现有 RR 闭环上实现了可选 CPU 并发搜索。
每个 worker 使用只读快照生成候选；一个控制线程按固定
`(epoch, priority, task_id)` 顺序检查、提交。它复用 PR 的确定性事务原则，
不把这种复用本身列为新的研究贡献。

读取日志包括所有影响出口选择和搜索的资源，包含未选中的候选与失败搜索，
而不只是最终路径。提交前先核对全部读取版本和写入容量/版本上限；全部
通过才更新权威状态。失效的成功或失败候选都重新读取当前权威状态并搜索，
防止旧 shadow 造成错误路径或错误的“不可达”。候选生成不占用权威容量；
边界预留采用乐观版本验证，在固定提交点兑现。
旧摘要也可能使代价溢出而当前状态并不溢出：候选保留异常前的读取日志和
搜索工作量，先验证版本，再对过期候选重放；当前快照的溢出仍拒绝且不写入。
该情况在修改前冻结实现上已复现，修复后有定向回归与 sanitizer 检查。

边界 shadow 只保存 capacity、occupancy、version 与 present/history 成本，
没有可写的 net owner。owner 查询来自窗口开始时的权威快照；若边界摘要
较旧，候选继续携带旧版本，必须重放后才可能提交。发布消息按版本单调
应用，重复消息幂等，晚到旧消息丢弃，同版本不同内容拒绝。参考策略向
所有非 owner die 广播边界摘要，尚未优化订阅范围。

```bash
python3 tools/run_rr_pair.py work/new_native_case work/new_pr_reference work/new_pair \
  --modes downstream_bounded --native-base-costs work/new_native_costs \
  --cost-model vpr_style --cost-bits 64 \
  --speculative-workers 4 --shadow-sync-windows 3
```

`--speculative-workers 0` 是原串行默认；正值启用 1–32 个 CPU worker。
`--shadow-sync-windows N` 每 N 个投机窗口发布最新边界摘要。host 同名环境
变量为 `DIEROUTE_SPECULATIVE_WORKERS`、`DIEROUTE_SHADOW_SYNC_WINDOWS`。
配置、执行方式与计数均写入 JSON，`.transactions.csv` 保存固定提交顺序、
初始/最终状态、读取日志哈希、重放标志与路径哈希，参与五次重复检查。
完整/有界搜索的读取日志可以不同，但最终七类路由/控制产物必须一致。

四 worker、发布间隔三窗口的固定关键度开发集，各完成五次和原生检查：

| 案例 | 迭代 | 冲突重放 | 边界摘要消息 | 摘要 payload 字节 | 与串行七类路由产物 |
|---|---:|---:|---:|---:|---|
| diffeq | 6 | 2,679 | 163,859 | 5,243,488 | 逐字节相同 |
| alu4 | 6 | 2,725 | 105,854 | 3,387,328 | 逐字节相同 |
| ex5p | 14 | 3,633 | 242,756 | 7,768,192 | 逐字节相同 |

见 [`speculative_cohort_audit_20261013.json`](experiments/speculative_cohort_audit_20261013.json)。
U280 原生七节点邻域也完成四模式、三组任务、各五次并发验证；合法结果和
预期容量竞争失败均与串行一致。定向测试另覆盖未选中出口的版本变化、旧
失败候选恢复可达、最后一次写入溢出无副作用、乱序 shadow 消息，以及
1/2/4 worker 与不同同步周期下的完整 PR 共享树闭环。

表中的消息统计已应用的摘要更新，按声明的 32-byte 逻辑 payload 计数，
**不是实测 HBM/链路流量**，
不包含队列封装、传输协议或 CPU 快照复制。当前 worker 复制完整 CPU
快照，shadow 在 CPU 内存中稠密分配，权威状态仍由一个控制线程更新。
因此这里只证明参考协议的确定性与正确性，没有证明硬件并发提交、
HBM 映射、带宽节省或加速比；原有联合 WL/CPD 失败结论也没有改变。

同一 diffeq 输入还比较了每窗口发布与每三窗口发布，均五次确定、原生
合法且七类最终路由产物一致。每窗口发布为 163,903 次摘要更新、2,376 次
重放；间隔三窗口只减少 **0.027%** 的摘要 payload，却增加 **12.75%** 的
重放。因此默认仍为每窗口发布，不能根据“少发消息”推断性能更好。见
[`speculative_sync_ablation_20261013.json`](experiments/speculative_sync_ablation_20261013.json)。

## 完整 U280 DCP 已用资源与背景占用

`tools/DcpRouteFootprint.java` 从完整 routed DCP 和显式可读 EDIF 导出所有
net 的引脚、PIP、节点成员线、owner 和分区引脚。以整个原生电气节点作为
资源；其代表 wire 只决定稳定标识，SLR membership 来自全部成员 wire。
每条成员 wire 都重新调用原生 `Node.getNode` 验证身份。源引脚节点也进入
占用清单，不能沿用部分软件路径只计子节点的规则而遗漏背景源资源。

2026-10-13 的完整设计导出与独立 C++ 核验结果：

| 项目 | 数量 |
|---|---:|
| 物理 net / site pins | 963,825 / 2,928,754 |
| 原生 PIP / 已用电气节点 | 11,500,192 / 12,201,318 |
| 节点成员 wire | 34,653,665 |
| 暂定候选 net / source-sink 任务 | 418,310 / 1,194,028 |
| 候选跨 SLR 端点任务 | 12,720 |
| 原有有向 PIP 上不可达的候选 sink | 0 |
| 跨 net 共占节点 / 候选与背景共占节点 | 0 / 0 |
| 分区引脚 / 候选 net 触及分区引脚 | 261 / 0 |
| 已用跨 SLR Laguna 节点 | 15,502 |
| 候选 / 背景 net 占用的 SLL 节点 | 4,680 / 10,822 |

SLL 分边界计数为 SLR0–1：9,747，SLR1–2：5,755，分别与先前 Vivado
utilization 报告一致。任务数与 SLL 数不是同一指标：同一 net 的多个 sink
可以共享路由树。候选 net 中 416,553 个位于 `level0_i/ulp/`，另有 1,757 个
位于其外；目前没有据此挑选实验子集。

`verify_dcp_footprint.cpp` 独立重算所有成员归属、SLR mask、PIP 端点身份、
owner、完整任务覆盖和有向可达性，验证反向 PIP、原生代表节点和分区标记。
`audit_dcp_footprint.py` 再逐条匹配此前独立物理 inventory 的全部 net/pin
记录，核对原生 SLL 报告与输入、依赖、产物哈希。14 个手工图/破坏测试和
ASan/UBSan 均通过；方向翻转测试必须报告不可达，不能只检查表结构。

```bash
python3 tools/run_dcp_footprint.py --dcp input.dcp --edif readable.edf \
  --output work/new_footprint --jdk /path/to/jdk --cufr /path/to/cufr \
  --runtime /path/to/isolated/rapidwright/runtime
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror \
  tools/verify_dcp_footprint.cpp -o /path/to/verify_dcp_footprint
python3 tools/audit_dcp_footprint.py --producer work/new_footprint \
  --inventory work/previous_native_inventory/inventory \
  --utilization work/native_baseline/reports/utilization.rpt \
  --verifier /path/to/verify_dcp_footprint --output work/new_footprint_audit
```

此导出是诊断中间格式，不是 production ABI；二进制是无 header 的 LE u32
定长记录，缺失 ID 为 `0xffffffff`，由 manifest 固定 schema 和哈希。记录
宽度依次为：`nodes/nets` 64 B，`pips/tasks` 32 B，`pins` 16 B，`wires` 12 B，
`owners` 8 B。接入生产数据面时仍须转换、验证版本化 ABI，不能直接加载。

候选筛选排除静态/时钟及需时钟资源的 net、无源/多源、固定或 route-through
PIP、stub、缺失节点、无 sink 和直接同节点连接。所有排除项仍保留完整背景
占用，owner 表不会覆盖旧 owner 或把它静默丢弃。候选仅表示通过这些筛选，
不等于已经证明全部重路由约束或时序模型正确。当前完整导出无缺失节点。

原始导出：`work/u280_dcp_footprint_v1_20261013/`；交叉审计：
`work/u280_dcp_footprint_cross_audit_v1_20261013/`；冻结证据见
[`dcp_footprint_progress_20261013.json`](experiments/dcp_footprint_progress_20261013.json)。
这完成了已有路由的资源与背景清点，尚未导出全部未占用邻接、接入真实
商业延迟/容量、把背景状态接入 controller 或运行 DieRoute DCP 重路由。
原有联合 QoR 失败与硬件待验收状态保持不变。

## U280 全器件原始拓扑与 DCP 映射

`NativeDeviceGraph.java` 逐一枚举所有 tile wire，以原生 `Node.getNode` 返回
的身份分组，覆盖未占用资源和孤立节点；随后枚举全部原生 PIP。输出保留
时钟、静态和 route-through 类资源及缺失端点标记，不把原始拓扑直接当作
所有设计均可使用的搜索图。

| 完整器件导出项目 | 数量 |
|---|---:|
| tile / tile wire | 615,440 / 269,838,154 |
| 电气节点 / 有效成员 wire | 91,975,782 / 269,570,361 |
| 没有有效 Node 的 wire | 267,793 |
| PIP / 双向 PIP | 427,282,568 / 432,576 |
| route-through PIP / 缺少有效节点端点的 PIP | 15,945,120 / 321 |
| 跨 SLR Laguna 节点 | 46,080（两条边界各 23,040） |

全器件扫描发现 336 个 `getAllWiresInNode()` 返回空列表的节点。定向复查
发现静态 `Node.getWiresInNode(tile, wire)` 在样例上还会返回属于其他节点
或无法解析的 wire，因此没有使用该接口作补全。当前适配器从每条 wire 的
原生身份重建完整成员集，并核对全部非空实例成员列表；336 个例外显式
标记并保存。独立核验确认它们均不连接任何已枚举 PIP，也不出现在原 DCP
已用节点中。初次失败和定向诊断保留在
`work/u280_native_device_graph_v1_20261013/`、
`work/native_empty_node_probe_20261013/`。

`verify_native_device_graph.cpp` 独立重算所有 wire 覆盖、节点 membership、
几何边界、原生代表身份和 PIP 端点。原 DCP 的 **12,201,318 个节点、
34,653,665 条成员 wire、11,500,192 个 PIP 全部逐项匹配**，无重复 PIP
记录或歧义匹配。映射保留 5,303,529 个背景节点、6,897,789 个候选节点和
261 个分区引脚标记。10 项手工图/破坏测试及 ASan/UBSan 均通过。

```bash
python3 tools/run_native_device_graph.py --device xcu280 \
  --output work/new_device_graph --jdk /path/to/jdk --cufr /path/to/cufr \
  --runtime /path/to/isolated/rapidwright/runtime
g++ -std=c++17 -O2 -Wall -Wextra -Wpedantic -Werror \
  tools/verify_native_device_graph.cpp -o /path/to/verify_native_device_graph
python3 tools/audit_native_device_graph.py --graph work/new_device_graph \
  --footprint work/new_footprint --verifier /path/to/verify_native_device_graph \
  --output work/new_device_graph_audit
```

原始拓扑约 22 GiB，是尚未压缩的诊断中间格式，**不是已能装入 HBM 或
完成搜索的数据面**。所有表均为 LE u32：`nodes.bin` 64 B、`pips.bin` 32 B、
`wires.bin` 12 B、`null_wires.bin` 8 B；v2 的成员表按 tile/wire 排序，节点
记录的字段和 flags 与 DCP footprint 不同，不能混读。核验器生成两个 u32
ID 映射表和 32 B 的 `occupied_nodes.bin`，保留原有 owner/背景/分区信息，
未凭空赋予可用容量或时序代价。完整字段定义见
[`native_device_graph_schema_v2.json`](experiments/native_device_graph_schema_v2.json)。

原始导出与交叉核验分别在 `work/u280_native_device_graph_v2_20261013/` 和
`work/u280_native_device_graph_audit_v1_20261013/`；证据见
[`native_device_graph_progress_20261013.json`](experiments/native_device_graph_progress_20261013.json)。
下一步必须建立设计允许的邻接、明确并行 PIP 的路径身份、压缩/索引原始
拓扑，并接入真实商业延迟、背景保护和 DCP 重路由。全图数量和原路由映射
不构成新算法合法性、QoR、加速或功耗结论。

## 保留 PIP 身份的完整有向 CSR

`build_native_csr.cpp` 将原生 PIP 表转换为可遍历的有向邻接。每条弧保存
`destination` 和 `(PIP ID << 1) | direction`，双向 PIP 保留两个方向；同一
节点对的不同 PIP 不合并。缺少端点的 321 个 PIP 明确写入排除清单，原始
记录保留。route-through、时钟等资源尚未按设计约束筛选。

独立核验覆盖完整输入，结果为 **427,714,823 条弧**、85,382,442 个有出边
节点、最大出度 739。存在 **43,884 组平行弧**，均有两条弧；抽查包括 INT
tile 内由不同 wire 驱动同一目标的不同 PIP。因此旧 RR 后端只保存节点路径
且拒绝平行 PIP 的限制不能直接绕过。下文新增显式接口已让搜索、共享树和
输出保留边身份；完整商业设计回写仍未完成。
原 DCP 的 11,500,192 个 PIP 在 CSR 中逐一匹配使用方向，包括 5,588 个
反向使用的 PIP。

输出三个文件均采用共享的 64 B `FPGAACCP` header，包含 schema、对象类型、
记录数、payload 长度、架构 SHA-256 的 128-bit 前缀、CRC64 和 endian 标志。
`offsets.bin` 为 u64 前缀和，`arcs.bin` 每弧 8 B，`protection.bin` 每节点
1 B；schema 及完整 SHA-256 仍由 manifest 冻结。这些是新增的诊断对象
类型，不代表原 HLS kernel 已支持该格式。

三个文件合计 **4,249,500,822 B（约 3.96 GiB）**，不含原生目录、几何、
时序代价、可变资源状态、共享树或硬件队列，不能据此宣布完整设计能装入
HBM。保护标记保留背景 owner、分区引脚、静态绑定和成员 getter 例外。
额外检查确认全部候选 net 的 **1,612,338 个引脚、6,479,479 个原有 PIP**
均不触及任何保护标记；这证明这些标记不会阻断原有候选连接，尚未证明
控制器已经实施保护或新搜索路径满足全部商业约束。

```bash
cmake -S . -B build -DCMAKE_BUILD_TYPE=Release
cmake --build build --target dieroute_native_csr_build dieroute_native_csr_verify -j2
ctest --test-dir build -R '^native_csr$' --output-on-failure
python3 tools/run_native_csr.py --graph work/new_device_graph \
  --mapping-audit work/new_device_graph_audit --footprint work/new_footprint \
  --builder build/dieroute_native_csr_build --verifier build/dieroute_native_csr_verify \
  --output work/new_native_csr
python3 tools/audit_candidate_protection.py --csr-run work/new_native_csr \
  --output work/new_candidate_protection_audit
```

手工图以独立字节 oracle 核对方向、平行边、自环和保护位；另包含带重新
计算 CRC 的语义破坏测试，防止仅靠 checksum 判为正确。11 项测试和
ASan/UBSan 均通过，并已注册 `native_csr` CTest。完整图输出和核验见
`work/u280_native_csr_v1_20261013/`，候选保护检查见
`work/u280_candidate_protection_audit_v1_20261013/`；字段定义和冻结证据分别见
[`native_csr_schema_v1.json`](experiments/native_csr_schema_v1.json)、
[`native_csr_progress_20261013.json`](experiments/native_csr_progress_20261013.json)。

## 显式 PIP 边路径（2026-10-13）

新增 `EdgeBatchResult`、`execute_edges` 和 `route_wide_pathfinder_edges`。
搜索记录实际 CSR 边，平行边等价时按边 ID 确定选择；共享树保存该边，
树种子的上游时延由所选边累计。rip-up 清除节点与边路径，冲突重放同时
替换两者。完整任务路径包含共享前缀，树输出每个 net/child 只记录一次。
路由与事务哈希均覆盖边 ID，固定图下不同 PIP 不再产生相同的节点路径哈希。

主机用 `DIEROUTE_EDGE_IDENTITY=1 DIEROUTE_COST_BITS=64` 启用该接口，新增
`.path_edges.csv`、`.tree_edges.csv`。原生图必须同时提供 `.edge_ref`：每个
CSR 边一个 u32 小端 `(catalog_pip_id << 1) | reversed`；不要按节点对反查。
ID 属于冻结的具体 PIP 目录，子图目录可以重编号，不能与完整器件目录混用。
`tools/pack_native_slr_graph.py --edge-identity` 可产生功能子图的该文件。
旧接口仍拒绝原生平行 PIP，显式接口不能把结果静默降为节点路径。当前主机
也拒绝在显式模式使用旧的节点路径外部 timing 命令；C++ 的
`EdgeTimingAnalyzer` 已有完整边路径参数，商业时序校准和适配器仍待实现。

12 项 CTest、核心 ASan/UBSan 和并发 TSan 均通过。测试覆盖平行边实际选择、
原子拒绝错误边、共享树时延、时序更新后换边、反向 PIP、1/2/4 worker 重放
及五次重复。三个冻结的开发用例各回放一次，七类语义输出及原有非耗时
计数与之前完全相同；保留旧模式哈希格式，不将新旧格式的哈希直接比较。

另从原生数据库导出 `INT_X0Y719` 的两个不同 PIP，它们具有相同电气端点。
对这对 PIP 施加两组人工代价以分别选中，并与已有七节点 SLR 子图一起做
400 次运行。560 条输出路径中的 960 次 PIP 使用重新在 RapidWright 器件
数据库解析通过，损坏 PIP 被拒绝。此处只验证电气身份、容量协议与确定性，
**不证明完整设计合法性、商业时延或 QoR**。完整图的 43,884 组平行弧尚未
作为完整设计被该控制器路由。

字段契约见 [`edge_identity_schema_v1.json`](experiments/edge_identity_schema_v1.json)，
冻结证据见 [`edge_identity_progress_20261013.json`](experiments/edge_identity_progress_20261013.json)。

## 背景保护与引脚独占准入（2026-10-13）

新增共享只读 `RoutingPolicy`，将硬性禁止与可协商的拥塞占用分开。
受保护节点、禁止的 PIP 和其他 net 的专属引脚不能用于局部搜索、全图回退、
下游反向搜索或 corridor；即使 PathFinder 允许临时超用也不能绕过。
提交重新检查路径，控制器再次检查成功分支。保护节点的占用、owner、容量、
版本和逻辑宽代价在初始化、rip-up、代价增长后保持不变。测试中使用耗尽的
背景版本号，抓到了初始化漏用保护规则的问题，已修正并保留失败日志。

主机检测 `.node_protection`、`.terminal_net`、`.edge_protection` 三项
sidecar；任一存在即要求三项齐备并启用显式边路径和 64-bit 代价。
前两项按 PR 节点排列，后一项按 PR CSR 边排列。完整 native 导出的
`pip_protection.bin` 则按 PIP 目录排列，转换时必须通过 `edge_ref >> 1`
展开，不能直接当作 CSR 边数组使用。

`build_native_policy.cpp` 已扫描完整 U280 原生图。它保留已核验的背景、
分区引脚、常量绑定和空成员保护，增加时钟 intent 禁止，并屏蔽 route-through、
fixed/stub 和缺失端点 PIP。全部候选引脚节点固定其 net 访问权，rip-up 时
也不释放给其他 net。完整检查结果为：

- 5,886,862 个受保护节点，1,612,338 个独占候选引脚节点。
- 15,945,441 个受限制的原生 PIP；352,071,611 条弧通过这一级静态检查。
  这些弧仍需满足 net 访问权及其余 site/tile 规则，不能全部视为设计合法。
- 全部 1,612,338 个候选引脚、6,479,479 个原始候选 PIP 和
  1,194,028 个任务通过准入检查，无需放宽规则来容纳原始路径。
- 本 DCP 候选端点均属于单一 SLR，12,720 个任务跨 SLR。
  117,570 个候选源节点具有原生入边；准入不要求源节点是图论上的根。

15 项 CTest、核心 ASan/UBSan 与 TSan 通过；新增主机测试覆盖 48 种
模式/worker/准入情形，原生数据构建器有 9 项独立字节及破坏测试。
三个冻结开发用例的七类语义输出和原有非耗时计数仍完全一致。
完整 native 策略的表项和计数另以独立转换核验脚本重算。

```bash
cmake --build build --target dieroute_native_policy_build -j2
python3 tools/run_native_policy.py --csr-run work/new_native_csr \
  --builder build/dieroute_native_policy_build --output work/new_native_policy
# 使用安装了 NumPy 的 Python；仅做转换/计数核验，不运行被测路由算法。
python3 tools/audit_native_policy.py --run work/new_native_policy \
  --output work/new_native_policy_independent_audit
```

完整导出位于 `work/u280_native_policy_v1_20261013/`。字段与冻结证据见
[`native_policy_schema_v1.json`](experiments/native_policy_schema_v1.json)、
[`routing_policy_progress_20261013.json`](experiments/routing_policy_progress_20261013.json)。
完整图上的原始路径准入检查不等于完整图重路由；商业 site/tile 限制、
真实容量/时延、完整数据打包、DCP 回写和原生 QoR 仍待完成。

## 固定引脚访问与完整原生搜索图（2026-10-13）

新增 C++ 访问分析器、搜索图构建器和独立验证器。核心路由节点按 SDK 的
native representative tile 分类为 INT/LAG_LAG/LAGUNA_TILE；不能用规范化
成员列表中的首个 tile 代替。其余原始候选节点保持 net 专属，只允许原设计
中出现过的有向 PIP 作为引脚访问路径。原始 core→noncore 接入点也保留给
对应的 sink net。背景、时钟、分区引脚、route-through 等既有禁止规则继续生效。

完整 DCP 的 418,310 个候选 net 中，430,659 个非核心连通分量均包含候选
端点，没有非端点中转分量；其中 6,424 个是无需进入核心路由图的直接连接。
固定访问包含 461,012 个非核心节点、498,066 条有向 PIP；另有 12,349 个
核心节点作为固定 sink 接入点。源访问可以保留多条原始出口，不强行简化为
一个投影节点。本模式固定原有 site/pin 选择，不支持新增 LUT 输入交换或
替换源输出，后续基线比较必须披露这项约束。

Laguna 输入分类另用 SDK 直接导出核验：所有 UBUMP 节点的两级上游 INT
NODE_PINFEED 都应纳入，包含器件边缘的单 SLR UBUMP。旧构图仅从跨 SLR
根节点出发，漏掉一部分输入；虽然原始候选 PIP 仍全部保留，独立 SDK 核验
拒绝了旧图。失败图和日志保存在 `work/u280_native_search_v1_sdk_rejection_20261013/`。
这说明“保留原始路径”本身不足以验证完整搜索空间。修正版及 SDK 输入分别
保存在 `work/u280_native_search_v2_20261013/` 和
`work/u280_laguna_inputs_sdk_v2_20261013/`；单 SLR 边缘节点不计作跨 SLR 资源。

修正版含 253,648,514 条搜索弧，独立验证器逐条扫描 427,714,823 条原始弧
后确认结果一致；6,479,479 个原始候选 PIP 全部保留。SDK 的 115,200 个
Laguna 输入和 69,120 个 UBUMP 节点身份完全匹配，其中 23,040 个 UBUMP
仅属于一个 SLR，跨 SLR 节点仍为 46,080 个。17 项 CTest 通过，新增工具
的 7 项访问分析、12 项构图/破坏用例通过；访问分析器、构图器和独立验证器
也通过 ASan/UBSan 测试。

```bash
cmake --build build --target dieroute_native_access_analyze \
  dieroute_native_search_build dieroute_native_search_verify -j2
python3 tools/run_native_access.py --policy-run work/new_native_policy \
  --analyzer build/dieroute_native_access_analyze --output work/new_native_access
python3 tools/run_native_laguna_inputs.py --graph-run work/new_native_device_graph \
  --output work/new_sdk_laguna_inputs
python3 tools/run_native_search_graph.py --access-run work/new_native_access \
  --builder build/dieroute_native_search_build --output work/new_native_search
python3 tools/audit_native_search_graph.py --run work/new_native_search \
  --sdk-run work/new_sdk_laguna_inputs --verifier build/dieroute_native_search_verify \
  --output work/new_native_search_audit
```

独立验证器从原始引脚/PIP 重建专属访问权，核对 SDK 节点身份，并扫描全部
原始弧，要求输出 CSR 恰好是规则允许的有序子序列。CSR 保留全器件节点 ID
和完整 PIP 身份；运行时仍须按当前 net 检查专属访问权，不能只检查边是否
存在。此处没有加入人工单位容量或单位时延，也没有完成全设计重路由。
字段契约见 [`native_search_graph_schema_v1.json`](experiments/native_search_graph_schema_v1.json)，
最新结果见 [`native_search_progress_20261013.json`](experiments/native_search_progress_20261013.json)。

## 稀疏搜索工作空间与完整图接入（2026-10-13）

`SparseSearch` 现在同时用于现有 RR 控制器的正向搜索和完整 native CSR
探测。标签表采用带 epoch 的开放寻址表，只为实际触达节点建立记录，按峰值
访问量保留存储；每次搜索重置 epoch，不扫描全器件节点。回绕时清除的是
已分配的哈希表。RR 的反向预估标签、portal 入口代价和读集去重也改为稀疏
记录。线程各自持有工作空间；这一阶段仍有资源快照、完整拓扑及 boundary
shadow 数组。后文“只读状态视图”进一步移除了每个 worker 的完整可变状态
副本，但没有消除所有全图内存开销。

保持原有代价、种子、闭集和 PIP tie-break 规则。3,000 组随机图与修改前
密集标签算法的路径、成本、边身份及计数一致；三个冻结开发用例的七类输出
和全部非耗时计数一致。初版漏记了抛出溢出异常之前的工作量，现已修正并保留
失败日志。19 项 CTest、7 项 ASan/UBSan 和 3 项 TSan 测试通过。一次 CPU
复跑比历史记录慢约 10–18%，不是速度提升证据，也不是受控性能对比。

`probe_native_search.cpp` 直接读取完整 91,975,782 节点、253,648,514 弧
的映射文件，以 net 专属权限过滤访问。探测只使用**跳数**，不把单位增量
解释成容量、拥塞代价或时延。按原始任务顺序为九种 SLR 方向组合各取两个
任务，固定这 18 个任务，将标签上限从 250,000 扩至 2,000,000 后各跑五次：

- 7 个任务找到路径，其中 1 个跨 SLR；另 11 个任务预算耗尽，结论未定。
- 五次路径、PIP 身份和搜索计数完全一致；独立脚本从原生 PIP 目录重查
  全部 340 次 PIP 使用，并检查 CSR、net 访问权、无环性及跨 SLR 节点。
- 标签/哈希表/队列最多保留 125,829,120 字节（120 MiB）；该数不包含
  图映射、输入目录、路由树、占用状态、读集或其他进程内存。

预算耗尽独立于不可达状态。通用搜索仍保留原来的单标签 cost/hops 语义，
不是带跳数约束的 Pareto 最短路求解器；探测以不约束实际路径的最大跳数运行。
完整原生图接入目前仅验证单任务连通性，尚无多 net 拥塞协商、完整设计闭环
和真实时序。未经检查的 CSR 也不能绕过冻结搜索图的前置独立核验。

```bash
cmake --build build --target dieroute_native_search_probe -j2
python3 tools/run_native_sparse_probe.py --search-run work/new_native_search \
  --independent-run work/new_native_search_audit --probe build/dieroute_native_search_probe \
  --max-labels 2000000 --per-pair 2 --repeats 5 --output work/new_sparse_probe
python3 tools/audit_native_sparse_probe.py --run work/new_sparse_probe \
  --output work/new_sparse_probe_audit
```

结果与边界见 [`sparse_search_progress_20261013.json`](experiments/sparse_search_progress_20261013.json)，
冻结来源与验证记录保存在 `work/sparse_search_verification_20261013/`。

## 聚合图下界与跨 SLR 搜索（2026-10-13）

新增以原生 `(tile, intent)` 为键的聚合图，含 951,990 个组和
6,878,474 条有向连接。独立验证器逐项检查原生节点和全部 253,648,514 条
搜索弧，保证跨组连接既不遗漏也不凭空增加。聚合只用于距离下界：完整搜索
仍使用原生 PIP，逐节点检查 net 访问权，没有从聚合图直接生成线路。

设 `H(n)` 为节点所在组到目标组的最少跳数。每条原生边要么留在同一组，
要么在聚合图有对应边，因此 `H(u) <= 1 + H(v)`，目标的下界为零。
`SparseSearch::run_guided` 以 `g+H` 排序，现有 RR 模式默认仍为零下界。
这里的 `H` 只适用于当前跳数目标；不能直接用于可能含零代价边的物理时延
或拥塞目标。SDK 的节点时延估算还涉及前驱 long-node 修正，尚未完成商业
时延标定与原生时序闭环。

对原来固定的 18 个任务、相同的 2,000,000 标签上限，各执行五次：

| 模式 | 找到路径 | 预算耗尽 | 详细图边访问 | 聚合图边访问 |
|---|---:|---:|---:|---:|
| 零下界 | 35/90 | 55/90 | 312,427,870 | 0 |
| 完整聚合距离 | 90/90 | 0/90 | 30,855,765 | 578,197,235 |
| 截断到源组距离 | 90/90 | 0/90 | 30,903,520 | 190,184,935 |

截断版本在反向 BFS 取出源组时停止，返回 `min(H, H(source))`；未发现组
取截断值。这仍是一致下界，同组源和目标退化为零下界。其预处理减少约 67%，
所有完成路径保持相同最少跳数。每个模式的 90 次聚合查询还初始化了
85,679,100 个距离槽位；上述边访问计数不包含初始化指令、载入、哈希校验
或索引构建。不同模式完成任务数不同，这些计数不能解释成等工作量加速比。

独立脚本重新解析完整聚合版本及截断版本各 2,250 次 PIP 使用，检查路径、
专属访问权、CSR 和五次重复一致性；每个版本包括 60 条跨 SLR 路径。
聚合索引四个二进制文件共 410,649,128 字节。固定任务集的详细搜索工作空间
最多 128 MiB，另有最多 8,002,264 字节聚合距离/队列存储；不包含映射文件、
路由树和完整可变状态，也不是 HBM 可行性或板卡性能证明。

另按每种 SLR 方向组合前 16 个任务扩展为 144 个任务，单次运行中完整与
截断版本均完成 140 个，任务 213、216、220、221 仍达到标签上限。该集合
来自同一个 DCP，包含原来的 18 个任务，并非预留设计验证集；预算失败仍保留。
20 项 CTest、7 项 ASan/UBSan、3 项 TSan 通过。测试包含 1,500 组带权图与
Bellman–Ford 的最优代价对照、聚合表字节/破坏验证以及 49 对源目标的截断
等式和边一致性检查。三个冻结开发用例的七类输出及非耗时计数保持一致。

```bash
cmake --build build --target dieroute_native_quotient_build \
  dieroute_native_quotient_verify dieroute_native_search_probe -j2
python3 tools/run_native_quotient.py --search-run work/new_native_search \
  --builder build/dieroute_native_quotient_build --verifier build/dieroute_native_quotient_verify \
  --output work/new_native_quotient
python3 tools/run_native_sparse_probe.py --search-run work/new_native_search \
  --independent-run work/new_native_search_audit --quotient-run work/new_native_quotient \
  --source-radius --probe build/dieroute_native_search_probe --output work/new_guided_probe
python3 tools/audit_native_sparse_probe.py --run work/new_guided_probe \
  --output work/new_guided_probe_audit
```

字段和证明前提见 [`native_quotient_schema_v1.json`](experiments/native_quotient_schema_v1.json)，
冻结证据见 [`quotient_search_progress_20261013.json`](experiments/quotient_search_progress_20261013.json)。
该阶段闭合了固定探测任务的连通性问题；后续整 net 闭环见下节。

## 商业图整 net 共享树、协商与 DCP 回写

`NativeRouteState` 增加串行 C++ 稀疏权威状态：每个 net 保有共享树，同 net
的多个 sink 共用前缀只占用一次；不同 net 使用同一电气节点构成超用。源节点
计入占用并在 rip-up 时保留。接纳分支前完整校验 PIP、访问权限、父节点、深度
及版本范围；新记录预分配后发布，检查失败不产生部分更新。这里的单 net
电气独占规则不能代替通用 VPR capacity 或商业 site/mux 合法性。

原先 144 个独立探测任务关联 70 个 net，展开其所有 sink 后是 298 条连接。
路由时冻结全部未选 net 的 12,198,732 个原有电气节点，包括未选的 candidate
net。搜索从当前共享树各节点出发，新节点代价为
`1 + history + present × other_net_users`，因此聚合跳数下界仍有效；该代价没有
物理时延或线长单位。发生超用时更新 history，并对全部冲突 net 进行重路由。

最初整 net 版本停在 296/298：高扇出 net 的两个早期 sink 达到标签上限，
稍后形成的共享树未被用于重试。加入“树增长后仅重试失败 sink”后，同一
2,000,000 标签上限下，五次从初始状态运行均完成 298 条连接，三轮超用数为
2、1、0。所有重复的树、路径、占用、history/version 和迭代计数一致。
每次累计详细边访问 32,270,334 次，聚合预处理边访问 1,100,467,159 次；
后者及失败重试均保留，不能仅据详细搜索计数宣称加速。

独立审计解析五次运行的 12,640 条树 PIP、68,185 次完整路径 PIP 使用，
包括 1,210 条跨 SLR 路径。完整 23 项 CTest 和新增两项 ASan/UBSan 通过；
此新增权威状态是串行实现，没有据此新增分布式或硬件一致性结论。

`write_native_cohort.py` 将第零次运行的完整树转换为原生 PIP，通过 Java
只替换所选 net 的 PIP 列表，保留站点内连线；写出后独立重新加载。
70 个 net 中 44 个路径发生改变，所选 PIP 总数从 2,516 变为 2,528。
未选路由、全部受检物理引脚、site routing、BEL 放置/引脚映射、分区引脚
保持一致。逻辑网表虽有 SDK 标识符重命名，774,385 个叶实例和 4,537,722
个端点的完整连接导出与原始网表严格相等；约束、HWDEF 和 HDL stub 字节一致。
Vivado 2022.2 在未调用 `route_design` 修复的情况下，确认 640,797 个 routable
net 全部连通、路由错误为 0，默认 DRC 无 Error/Critical Warning；438 个
Warning 和 5 个 Advisory 与基准一致。SLL 总量仍为 15,502（两边界分别
9,747/5,755），与电气节点独立重算一致。setup WNS/TNS 为 +0.016/0 ns；
hold WHS 从 +0.006 降至 +0.004 ns，THS 仍为 0，不能宣称时序完全不变。
这里只对一份确定性输出做了原生检查；bus-skew 的后续成对验证见下节，
bitstream 验收仍未完成。
PIP 数不等于物理线长，也未据此通过联合线长/CPD 门槛。

```bash
python3 tools/run_native_cohort.py --search-run work/new_native_search \
  --independent-run work/new_native_search_audit --quotient-run work/new_native_quotient \
  --router build/dieroute_native_cohort --output work/new_cohort --repeats 5
python3 tools/audit_native_cohort.py --run work/new_cohort --output work/new_cohort_audit
python3 tools/write_native_cohort.py --run work/new_cohort --audit work/new_cohort_audit \
  --output work/new_writeback --jdk /path/to/jdk11 --cufr ../persistroute/third_party/cufr \
  --runtime work/isolated_rapidwright_runtime
```

状态契约见 [`native_route_state_schema_v1.json`](experiments/native_route_state_schema_v1.json)，
冻结证据见 [`native_cohort_progress_20261013.json`](experiments/native_cohort_progress_20261013.json)。
这仍是单个商业开发设计的 70-net 闭环，尚未完成全设计路由、校准时延目标、
原生 corridor/shadow 控制层接入、联合 QoR 验收及 HBM 硬件研究。

## 原生 bus-skew 与端点最小/最大时延

`run_native_timing.py` 对原始和上述回写 DCP 执行相同的只读 Tcl：全部
bus-skew 约束、两条指定路径的 setup/hold，以及 70 个 net 的各负载端点
四角值 `FAST_MIN/MAX`、`SLOW_MIN/MAX`。每次 144 项查询全部解析成功，
307 个逻辑负载引脚各有 total/interconnect 两组时延，合计 614 个对象；
`ESTIMATED=0`。原生 net delay 单位为 ps，TimingPath 属性单位为 ns。
逻辑引脚与物理 site-pin 任务的关系由后文独立连通性审计闭合；它不是一一映射。

独立审计逐项校验约束覆盖。SDK 回写后 21 项约束的 `get_cells` 集合成员
顺序改变，报告还有反斜杠换行；审计仅规范化可识别的 literal 集合，分别
保留 From、To 及全部成员，忽略源文件行号，其他表达式按原文比较。
392 项约束中，391 项有数值比较、均无违例，最小裕量 1.700 ns；另 1 项
仅一个端点，报告 `No bus skew paths found`，没有将其记为数值通过。
所有约束的覆盖和报告值在两个 DCP 间一致。

全设计 WNS 不变掩盖了局部时延变化：307 个负载中，慢角最大 net delay
增加 164 个、降低 103 个、不变 40 个，最大增加 **2,589 ps**。该端点属于
net 288522（`w.w_pipe/Q[0]`），时延由 5,171 增至 7,760 ps；这也是先前
需要共享树增长后重试的高扇出 net。数据只揭示关联，不证明退化由重试造成。
新全局最差 hold 路径的成对裕量为 **29 → 4 ps**，数据路径减少 29 ps，
required time 减少 4 ps；原来的最差 hold 路径仍为 6 ps。跳数/拥塞目标
尚未提供同时保护 setup 和 hold 的质量保证，不能据 bus-skew 通过宣布
联合时序/线长门槛通过。

```bash
python3 tools/run_native_timing.py --native-run work/native_checkpoint_checks \
  --selected-nets work/selected_nets.tsv --targets work/target_paths.tsv \
  --output work/new_native_timing
python3 tools/audit_native_timing.py --original work/original_native_timing \
  --routed work/new_native_timing --output work/new_native_timing_audit
```

## 只读状态视图与按边界存储的 shadow

`RRStateView` 借用权威 Resource/64-bit cost 数组；远端边界只保存不可变
摘要覆盖项，并从当前权威快照取得 net owner。读取版本仍进入完整 read
journal，所有 worker 完成读取后才按固定顺序提交和重放。它不是可独立
修改的资源副本；调用方必须在读阶段保持底层数组存活且不变。

`BoundaryShadows` 的 latest/replica 摘要由每个全图节点一项，改为每个
边界节点一项。若边界数为 B、die 数为 D，摘要记录数为 `(D+1)×B`；
静态 owner/boundary 标记仍与全图大小相关。10 万节点、2 个边界节点和
2 个 die 的结构测试确认只有 6 条摘要，每个视图仅复制 1 条远端记录，
内部节点的地址直接指向同一权威数组。静态拓扑和入边索引仍在 worker
之间复制。该阶段仅覆盖通用 RR；后文补充原生边界副本接入，原生 corridor
与硬件分布式同步仍待实现。

三个冻结串行开发案例保持原有输出和全部非耗时计数；`diffeq` 的 4-worker
投机运行在同步周期 1、3 下分别与旧版比较，新版各重复五次，八类产物及
全部非耗时计数一致。独立审计重新哈希 15 次运行和串行控制记录。24 项
CTest（含 10 项原生时序审计反例）、5 项 ASan/UBSan、1 项 TSan 通过。
这些结果支持功能等价和存储结构改进，没有据共享主机耗时宣称加速。

契约见 [`rr_state_view_schema_v1.json`](experiments/rr_state_view_schema_v1.json)，
冻结证据见 [`native_timing_shadow_progress_20261013.json`](experiments/native_timing_shadow_progress_20261013.json)。

## 原生时序引脚到物理任务的完整映射

`NativeTimingPins.java` 仅导出已有设计：逻辑/BEL 引脚映射、完整选中 net
的 site pin、相关站点的 net-labelled 导线及已用 site PIP，并调用 SDK
取得引脚的已路由 site-pin 关系。Python 独立沿导线驱动端和已选 mux 逆向
重建连接，拒绝环、多驱动、未选 mux、跨 net 或未支持的 route-through；
不选择新路径、不修改 DCP。所有物理引脚还须与原始 footprint 和先前 PIP
回写准备表完全一致。

307 个逻辑负载对应 307 个 BEL 输入：305 个通过 298 个 site 输入连接，
其中 291 个任务各有一个逻辑负载，7 个任务各有两个；另外 2 个是站点内
负载，独立追踪确认它们与 net 的输出 site pin 来自同一个功能 BEL 驱动端。
SDK 结果与独立追踪一致，298 条任务全部有原生延迟观测。站点路由与 BEL
映射在前次 DCP 回写/重载的完整快照中保持不变，所以映射适用于成对时延。
`task_delay_observations.csv` 保留每个逻辑负载的四角值，没有将共享一个
物理任务的多个负载取平均或将站点内负载虚构成跨站点任务。

原始 PIP 树与重路由树的路径对照覆盖全部 298 个任务：178 个跳数减少、
60 个增加、60 个不变。最大慢角延迟增加位于 net 288522 的任务 321，
路径从 63 跳增至 77 跳，`SLOW_MAX` 从 5,171 增至 7,760 ps；hold 敏感的
任务 28092 则从 14 跳减至 12 跳，`SLOW_MIN` 从 534 降至 505 ps。
跳数只是 PIP 数量；这些对照不能当成物理线长或证明某个启发式的因果效果。

```bash
python3 tools/run_native_timing_pins.py --timing-run work/original_native_timing \
  --footprint-run work/native_footprint --cohort-run work/native_cohort \
  --jdk /path/to/jdk11 --cufr ../persistroute/third_party/cufr \
  --runtime work/isolated_rapidwright_runtime --output work/new_timing_pins
python3 tools/audit_native_timing_pins.py --pin-run work/new_timing_pins \
  --cohort-run work/native_cohort --writeback-run work/native_writeback \
  --original work/original_native_timing --routed work/rerouted_native_timing \
  --output work/new_timing_pin_audit
```

字段与分类契约见 [`native_timing_pin_schema_v1.json`](experiments/native_timing_pin_schema_v1.json)，
证据见 [`native_pin_mapping_progress_20261013.json`](experiments/native_pin_mapping_progress_20261013.json)。

`run_native_load_slacks.py` 进一步对每个逻辑负载执行 min/max `-through`
查询，并对返回的 timing-path 对象保存属性和完整报告。260 个负载所在叶网段
与物理 net 名称不同；首轮严格字符串比较拒绝了它们，现用 Vivado `get_nets
-segments` 的完整成员集合核对，并冻结集合及直接网段作为证据。

原始与回写 DCP 各完成 614 项查询。每种 delay type 都有 284 个有限裕量
路径和 23 个报告 `Slack: inf` 的路径；后者的 SLACK、REQUIREMENT、
REQUIRED_TIME 属性为空，单独归类，不赋予零裕量或记为数值通过。两份报告
均没有未返回路径的查询，覆盖及有限/无约束分类一致。所有有限裕量都非负。
在这个负载集合中，最小 setup 裕量为 **1.434 → 1.433 ns**，最小 hold
裕量为 **0.029 → 0.004 ns**；这些是所选负载的路径统计，不是全设计 WNS。

任务 321 的 setup 裕量为 **13.913 → 11.325 ns**，仍有较大余量，hold
裕量为 2.158 → 3.546 ns（Fast corner）。任务 28092 的 hold 裕量为
29 → 4 ps（Slow corner），setup 裕量为 16.076 → 16.148 ns。
这说明较大的局部 net-delay 增量不能单独判定约束违例；优化时还须考虑
实际裕量及 hold 方向。614 对查询中有 14 对的最差路径起终点或 corner
改变；审计保留这些变化，未将全部裕量差解释成孤立 net 的可用时延预算。

```bash
python3 tools/run_native_load_slacks.py --native-run work/native_checkpoint_checks \
  --pin-run work/new_timing_pins --output work/new_load_slacks
python3 tools/audit_native_load_slacks.py --original work/original_load_slacks \
  --routed work/rerouted_load_slacks --mapping-audit work/new_timing_pin_audit \
  --output work/new_load_slack_audit
```

该阶段的 25 项 CTest 和 13 项站点连通性/别名/时序属性反例通过。上述工作
建立了原生时序观测到具体 C++ 路由任务的可核验关联；下面的反馈控制器
在此基础上执行候选验收与修复。搜索代价仍未完成物理时序标定，完整商业
设计的联合线长/CPD 门槛仍未通过。

## 原生 setup/hold 候选验收与修复

`NativeTimingController` 对冻结负载集合同时检查 setup 与 hold。每个观测
绑定完整候选树、固定设计/约束/映射上下文及 timing epoch；过期 epoch、
不同树、覆盖变化、缺失路径或非有限值冒充有限裕量都拒绝。有限裕量使用
精确的有符号整数 ps。默认拒绝 unconstrained 路径；本组实验显式允许原生
报告的 23 个 unconstrained 负载保持分类，不将其计作满足时序约束。

控制器在私有候选上完成检查，通过后整体发布；拒绝时权威树、占用、history、
version 和 epoch 均保持原值。这是串行的完整 checkpoint 发布边界：epoch
切换后必须丢弃旧视图，不能跨 checkpoint 仅比较 resource version。
尚未实现原生多 worker/shadow 的发布协议。

C++ 修复恢复低裕量负载所属的整条原始 net 树。如果原始树占用了其他候选
net 的资源，递归恢复这些 net，直到消除冲突。所有恢复在私有副本完成；
修复输出必须取得新的完整候选原生时序，不能沿用某条旧 net 的时延或裕量。
极端情况会恢复整个选中基线，并明确报告恢复集合。

70-net / 298-task 实例的三组政策回放及独立审计结果：

| 实验 | setup / hold 下限 (ps) | 初始候选判断 | 违反下限的 net | 恢复 net 数 | 输出树 PIP 数 |
|---|---:|---|---|---:|---:|
| zero_floor | 0 / 0 | 选中范围通过 | 无 | 0 | 2,528 |
| hold20 | 0 / 20 | 拒绝，产生待测修复 | 303585 | 5 | 2,542 |
| setup1434 | 1,434 / 0 | 拒绝，产生待测修复 | 454078 | 2 | 2,481 |

正裕量下限是开发集上的显式消融参数，不是用户要求、通用器件要求或已经
选定的测试集默认值。原始选中树为 2,516 个 PIP；PIP 数不是物理线长。
`zero_floor` 通过也不代表全设计联合 QoR 通过。

```bash
python3 tools/run_native_timing_feedback.py \
  --cohort work/native_cohort --cohort-audit work/native_cohort_audit \
  --mapping-audit work/native_pin_audit --timing-audit work/native_slack_audit \
  --writeback work/native_writeback --executable build/dieroute_native_timing_feedback \
  --output work/new_native_feedback
python3 tools/audit_native_timing_feedback.py \
  --run work/new_native_feedback --output work/new_native_feedback_audit
```

`write_native_cohort.py` 可用 `--feedback-run`、`--feedback-audit`、
`--feedback-case` 接收独立审计过的完整修复树。它仍只调用 Java 做 PIP
解析/回写与物理快照核对；所有路由树修改和修复决策在 C++ 中执行。
精确契约见 [`native_timing_feedback_schema_v1.json`](experiments/native_timing_feedback_schema_v1.json)。
新增反例覆盖 setup/hold 双侧拒绝、完整状态不变、过期/错树/错上下文观测、
覆盖变化、缺失路径、版本耗尽和三级资源冲突恢复。27 项 CTest 通过，其中
主机格式/绑定测试包含 10 个案例；两个相关 ASan/UBSan 测试也通过。

`hold20` 修复已走完新的 DCP 写入、SDK 物理重载、完整逻辑连接比较、Vivado
默认 route/DRC/timing 检查，以及相同 614 项逐负载查询。39/70 个 net 仍保留
新路由；640,797 个可路由 net 全部完成且没有路由错误，DRC 仍是 438 项
Warning、5 项 Advisory、零 Error/Critical Warning。SLL 为 15,502，与基线
一致，且原生计数与独立电气节点计数相符。全设计 WNS/WHS 为
**+0.016/+0.006 ns**，TNS/THS 均为零，恢复到原始基线的汇总值。

新逐负载结果中，最小 hold 裕量 **4 → 29 ps**，最小 setup 裕量保持
**1.433 ns**；每类仍有 284 个有限裕量负载、23 个明确 unconstrained
负载、零缺失路径。C++ 使用这些绑定修复树的新观测通过 `hold20` 验收，
原子发布 authority epoch 1；没有沿用初始候选的时序。修复 DCP 的 EDIF
文本存在差异，但 774,385 个叶实例及 4,537,722 个端点的完整连接比较
通过，全部 XDC/HWDEF/HDL stub 保持逐字节相同。
对同一修复候选及冻结的新时序观测再执行五次 C++ 验收，每次输出的 13 个
状态/决策文件逐字节一致。该复现不重复 Vivado 查询，也不冒充五次路由搜索。

本结果闭合的是这组开发负载的候选验收/恢复流程。修复候选的 bus-skew
扩展检查也已完成：392 项约束中 391 项可比较且全部通过，最小裕量为
1.700 ns；另 1 项只有单个端点，不计作数值通过。覆盖及报告值与原始设计
一致。工作负载 bitstream 验收现已完成，见下节；物理线长/CPD 联合验收和
板上性能仍未完成。
可复现入口是 `tools/verify_native_feedback_repair.py`，证据索引见
[`native_timing_feedback_progress_20261013.json`](experiments/native_timing_feedback_progress_20261013.json)。

额外的路径模型审计发现，37 条物理路径（对应 38 个逻辑负载）在初始重路由
前后具有完全相同的有向 PIP 序列。其中两条的其他树分支改变，原生
interconnect `SLOW_MAX` 却分别变化 +7 ps、−6 ps；完整 net 树未改变的
负载未出现时延变化。静态路径累加模型不能同时精确解释这些观测。此处
不将差异归因于某个特定电容参数。
路径证据保存在 `work/u280_native_path_model_limits_v2_20261013`。

新加入的 no-op 对照使用 SDK 序列化后、经五类完整物理清单逐字节核验的
原始设计，重放相同 Vivado 查询脚本。全部 614 个 net-delay 对象在
FAST_MIN/FAST_MAX/SLOW_MIN/SLOW_MAX 下均与原始值相同。因此，本次
对照未发现可观测的序列化时延偏移；它没有测出量化误差界或隔离电容参数。

原始、no-op、初始候选和修复候选四组观测进一步绑定各自完整路由树。
修复的 5 个 net 全部回到原始时延，另外 65 个 net 保持初始候选时延；
各组中完整树相同的全部负载也都没有时延变化。具体两个相同路径反例：

| 物理任务 | net | 原始 / no-op | 初始候选 | 修复候选 |
|---|---:|---:|---:|---:|
| 27983 | 303554 | 211 / 211 ps | 218 ps | 218 ps |
| 28255 | 303653 | 322 / 322 ps | 316 ps | 322 ps |

表中是 interconnect SLOW_MAX；两条源到负载路径在原始与初始候选间相同，
其他分支改变。第二条所在整网被恢复，时延也回到原值。完整数据包含两种
模式和四个 corner；不把 no-op 差值当作校正项，也不据此宣称静态路径代价
已经标定。四组对照见 `work/u280_native_delay_control_audit_v2_20261013`。

`analyze_native_delay_features.py` 用这些冻结观测做了一轮开发诊断。原始与
初始候选共有 305 个可映射逻辑负载，去除完整树/负载重复项后得到 578 行。
同一 net 的所有树及负载进入同一折；五折之间不共享 net。no-op 与修复
数据只用于对照，不增加训练样本。两种模型都使用固定 penalty=1 的 ridge，
归一化仅从训练折计算；路径模型使用 intent 计数和节点 tile 跨度等特征，
整树模型另外加入树规模、分支及路径外后代计数。

| SLOW_MAX 开发诊断 | 路径特征 | 路径 + 整树特征 |
|---|---:|---:|
| 逐负载 MAE | 141.09 ps | 247.13 ps |
| 按 net 等权 MAE | 56.78 ps | 55.45 ps |
| P95 绝对误差 | 748.78 ps | 792.99 ps |
| 最大绝对误差 | 899.91 ps | 875.89 ps |

高扇出 net 288522 占 236/578 行，是两种统计差异的重要来源。整树计数
并未带来一致改善，模型仍不能直接用作路由时延或裕量安全界。这里的
tile 跨度也不是标定物理线长；尚未充分表达缓冲、分支电气负载和站点内部
差异。分组交叉验证仍限于已经研究过的单设计开发集，不能算独立测试集结果。
模型参数、逐折名单、全部逐项预测和四个 corner 指标保存在
`work/u280_native_delay_feature_diagnostic_v2_20261013`。该 net 所在折的训练
数据最多有 33 个物理负载、177 个树 PIP；它的全部 236 行在这两项特征
及路径外后代计数上均超出训练范围，193 行的路径跳数也超出训练范围。
这暴露了开发覆盖不足，不能通过把同一 net 的负载拆到训练侧来改善指标。
新增求解器解析解、
最优性及 net 等权统计测试通过，全套 CTest 为 29/29。

```bash
python3 tools/analyze_native_delay_features.py \
  --control-audit work/native_delay_control_audit \
  --feedback-run work/native_feedback --mapping-audit work/native_pin_audit \
  --output work/new_delay_feature_diagnostic
```

进一步从已安装 SDK 导出两组树共有的 4,138 个节点。2,440 个节点取得
`RouterHelper.computeNodeDelay` 数值，1,698 个属于 helper 未建模而返回零的
类别；66 个跨 SLR 节点均在后者之中。这里的零不是物理零时延。导出同时记录
长线父子附加项、U-turn 排除惩罚和不支持状态，不以默认零填补错误。
首轮因独立 runtime 缺少 SDK timing 文本而失败；第二轮在输出目录建立独立
runtime，复制并绑定 SDK timing 文件哈希，保持共享 device cache 和上游源码
不变，已成功导出，且本组没有不支持或 U-turn 惩罚节点。

在完全相同的 578 行、整网分组五折上，SDK helper 分量累加、按 corner 的
仿射拟合、再加入跨 SLR 计数三种诊断的 SLOW_MAX 逐负载 MAE 分别为
461.03、320.18、228.71 ps；按 net 等权 MAE 分别为 213.65、405.04、
94.70 ps。结果没有超过此前路径特征模型。这些是 helper 分量的诊断，不能
视为完整 RWRoute 时序模型或物理 R/C 参数，也未用于改变 C++ 路由。
导出及诊断分别见 `work/u280_native_node_delay_v2_20261013` 与
`work/u280_native_sdk_delay_diagnostic_v1_20261013`。

## 工作负载 bitstream 验证

`run_native_bitstream.py` 接收已通过原生 route/DRC/setup/hold 检查的 DCP，
冻结输入与加载依赖，运行 factory `bitstream_checks` 和 `write_bitstream`。
它不调用 `route_design`，不修改约束或 DRC 严重级别，不执行器件编程。
`audit_native_bitstream.py` 在进程成功退出后核对全部输入/产物哈希、生成前后
路由计数、DRC 汇总、完整/局部 `.bit` 列表，以及每个文件的 tagged header、
payload 长度、器件标识和同步字。文件头检查不独立解码配置帧或验证硬件功能。

首轮脚本错误地假定 ruledeck 的 `SIZE` 属性等于 API 可枚举规则数，因此
在调用 `write_bitstream` 之前终止。独立空设计复核证明，当前 Vivado 2022.2
的 `SIZE` 为 6085，而两种官方规则枚举接口都返回相同的 6053 条规则；
空会话、U280 工程和已链接 U280 空设计均如此。修正版保存两种数量、验证
枚举结果一致，并直接运行完整 factory ruledeck，未用枚举列表替代实际 DRC。
失败日志保留在 `work/u280_native_hold_repair_bitstream_v1_20261013`。

第二轮已写出完整/局部 `.bit` 并打印 Bitgen 成功消息，但随后在 WebTalk
主机信息收集的 `libudev` 路径触发 `realloc` 错误，以 134 退出；缺少完成
标记及生成后路由检查，因此仍归类失败。容器 OOM 计数为零。小型本地复现
中，系统分配器枚举成功，加载 Vivado 自带 `libtcmalloc` 后发生 SIGABRT，
提前加载实际系统 `libudev` 后成功。这与
[glibc 的混合分配器 / RTLD_DEEPBIND 问题记录](https://sourceware.org/pipermail/glibc-bugs/2021-July/050637.html)
相符；本地复现证据在 `work/native_libudev_probe_20261013`。
恢复尝试通过 `--preload-libudev` 只改变新 Vivado 子进程的库加载顺序，并
绑定库文件哈希，不修改许可证检查、安装、全局用户设置、设计或 DRC。

第三轮完整运行已以 **退出码 0** 完成，生成后路由计数保持不变，640,797 个
可路由 net 全部完成且零路由错误。bitstream ruledeck 报告 222 项 Warning、
零 Error/Critical Warning；6053 条可枚举规则均启用，名称、启用状态和严重
级别与独立空设计参考完全相同。两个输出通过文件头、长度、器件、同步字
和哈希审计：

| 文件 | 字节数 |
|---|---:|
| `candidate.bit` | 50,943,997 |
| `candidate_pblock_dynamic_region_partial.bit` | 53,680,286 |

两份文件的配置 payload SHA-256 分别与第二轮写出的对应文件一致；生成时间
位于不同的文件头中。第二轮仍保留失败状态，不能以 payload 哈希相同追认其成功。
完整审计在 `work/u280_native_hold_repair_bitstream_audit_v3_20261013`，
本轮证据索引见 [`native_signoff_progress_20261013.json`](experiments/native_signoff_progress_20261013.json)。

```bash
python3 tools/run_native_bitstream.py --native-run work/native_checkpoint_checks \
  --preload-libudev /lib/x86_64-linux-gnu/libudev.so.1 \
  --output work/new_bitstream_run
python3 tools/audit_native_bitstream.py --run work/new_bitstream_run \
  --ruledeck-reference work/empty_design_probe/u280_linked_checks.tsv \
  --comparison-run work/previous_bitstream_attempt \
  --output work/new_bitstream_audit
```

该流程针对被重路由的工作负载，不是 DieRoute 加速器本身的 HLS/RTL/HBM
实现。即使生成通过，也不能据此关闭研究计划 G6/G7，或宣称 xclbin 部署兼容、
板上性能及能耗已经验证。

## 原生边界副本与完整读集重放

`native_boundary_shadow.hpp` 已接入原生共享树搜索。跨 SLR 电气节点保留完整
membership mask，以最低成员 SLR 作为摘要所有者；远端副本只含不同 net 的
占用数、history 和版本，不复制可写的 net 所有者集合。未使用资源采用明确
的全零初始值，释放后保留版本记录，整个检查点替换必须使旧视图失效。

每次搜索记录所有实际参与代价计算的远端边界资源，包含未被最终路径选中的
备选资源。提交前比较完整读集，过期结果先丢弃，再从当前串行状态重新搜索；
搜索失败、预算耗尽和溢出也经过同一验证流程。已有共享树节点继续作为源点，
不会重复计入本 net 占用。这个阶段以集中串行状态为权威；下节补充原生
corridor 的后续接入，并行 worker、die-local 分片权威及硬件同步仍待完成。

在同一 U280 原生图和 70-net / 298-connection 开发集上，直接读取权威状态、
每次搜索同步、每三次搜索同步各运行五次，均按 2→1→0 个过用节点收敛。
三种配置的完整树、共享前缀路径、占用、history 和版本逐字节一致；直接读取
模式还与此前归档的串行 cohort 输出一致。这里比较的是此前 C++ 候选树，
不是后续恢复五个 net 的 hold 修复检查点，本轮没有新增原生 STA 或 DCP 验收。

以下为每次重复的结果，通信计数包含结束时所有待发送摘要：

| 指标 | 每次搜索同步 | 每三次搜索同步 |
|---|---:|---:|
| 实际搜索次数 | 308 | 308 |
| 远端边界读记录 | 38,499 | 38,499 |
| 过期重放次数 | 0 | 4 |
| 最终保留边界摘要 | 36 | 36 |
| 逻辑摘要投递次数 | 88 | 86 |
| 搜索展开节点数 | 7,841,282 | 9,069,496 |

延迟同步只减少 **2.27%** 的建模投递次数，却增加 **15.66%** 的搜索展开量，
不支持加速结论。这些投递次数是广播模型计数，不是实测网络字节或 HBM 流量。
第一轮探索输出保留为 v1；其通信计数未清空结束时待发送更新，正式比较只使用
补齐最终同步及全图广播范围的 v2。独立核验覆盖原生有向 PIP、冻结外部占用、
完整读日志及最终副本与权威状态的一致性；30 项 CTest 和三项 ASan/UBSan
检查通过。证据见
[`native_boundary_shadow_progress_20261013.json`](experiments/native_boundary_shadow_progress_20261013.json)，
协议见 [`native_boundary_shadow_schema_v1.json`](experiments/native_boundary_shadow_schema_v1.json)。

```bash
python3 tools/run_native_cohort.py --search-run work/u280_native_search_v2_20261013 \
  --independent-run work/u280_native_search_v2_independent_20261013 \
  --quotient-run work/u280_native_quotient_v1_20261013 \
  --router work/native_boundary_build_20261013/dieroute_native_cohort \
  --shadow-sync-searches 3 --repeats 5 --output work/new_native_shadow_run
python3 tools/audit_native_boundary_shadow.py --baseline-run work/new_native_direct_run \
  --shadow-run work/new_native_shadow_run --output work/new_native_shadow_audit
```

直接读取对照使用同一二进制及输入，把 `--shadow-sync-searches` 设为 0，
并采用单独输出目录。该工作闭合了原生边界副本的串行参考链路；G2/G5 的
分布式实现与完整消融仍未完成，G4 的联合 QoR 门槛也未因此改变。

## 原生 corridor、候选比较与有界搜索

`native_corridor.hpp` 已接入相同的完整原生图。跨 die 转换发生在一个带完整
SLR membership 的电气节点内部，不增加虚构 PIP、重复占用或延迟。每段局部
搜索同时检查两个端点的 membership 和**真实 PIP 所属 SLR**，禁止顺便使用
未预留的跨 die 节点。失败后丢弃整个候选预留集合、重新选择通道；最终可回退
到原有全图搜索，保留必须离开再进入同一 die 的合法路径。

预留是串行候选记录，包含所选跨 die 节点及可能跨 SLR 的新 sink；共享树中的
SLL 不重复计数。协商阶段仍允许不同 net 暂时过用，最终收敛要求过用为零，
因此不能把这个实现称为严格的并发容量授予。所有成功候选都有完整有向 PIP
日志；失败、较差候选和异常都会释放其记录，只有完整选中分支才修改权威状态。
边界副本过期时，整个通道搜索和比较都重新执行。

可选的新入口比较将目标 die 内的延伸与从其他 die 新进入的完整增量分支比较。
搜索代价仍为 `1 + history + present × other_net_count`，几何距离只用于通道
提议排序。已有完整候选后，局部搜索以其代价减去前缀代价为上限，仅在
`g+h` **严格超过**上限时剪枝，保留等价候选。商图反向 BFS 同时截断在
`min(source_distance, C+1)`；所有可进入有界搜索的标签保持不变。
全 source/sink/radius 测试覆盖不可达分量，独立 Bellman–Ford 测试验证了
代价上限的可达性、最优代价及相等代价情况。

八种开发配置各重复五次，仍使用同一 70-net / 298-connection 工作负载。
下表为每次重复的主要结果；详细对照在
[`summary.csv`](work/native_corridor_comparison_v1_20261013/summary.csv)。

| 配置 | 树 PIP 数 | 详细搜索展开节点 | 商图展开分组 |
|---|---:|---:|---:|
| 全图基线 | 2,528 | 7,841,282 | 147,981,897 |
| 基础 corridor | 2,745 | 8,217,524 | 163,621,135 |
| 新入口比较，无代价上限 | 2,745 | 79,429,148 | 439,479,789 |
| 新入口比较，搜索及商图均有界 | 2,745 | 8,358,857 | 174,492,512 |

这些 corridor 配置均在两轮协商中按 12→0 个过用节点收敛，工作负载中没有
使用全图回退。所有 corridor 最终树相同，新入口比较没有找到更好的候选。
加入商图半径上限前，其展开量为 1,042,931,121；截断后减少 **83.27%**，完整
候选、路径、预留、边界读记录及最终状态逐字节不变。结合每三次搜索同步的
版本也保持结果一致，但每次重复需要 15 次重放，仍不能据此声称加速。

**质量门槛未通过。** 树 PIP 数比全图基线增加 8.58%，选中 SLL 仍为 36。
30 个 net 更换了 SLL 节点，所有 PIP 数增大的树都在这一组；这为下一步检查
通道排序提供了线索，但尚不能证明物理线长或时延变化的原因。PIP 数不是
物理线长，展开次数不是延迟；这些并发运行的实验也不构成 CPU 加速比测量。
本轮没有为新树执行 DCP 回写、原生 STA/DRC、bus-skew 或 bitstream 验收。

独立核验器重新构建每轮树、不同 net 占用、history、版本、发布快照及最终
边界副本，并检查所有完整候选的真实 PIP、代价和选择结果。31 项 CTest 与
6 项 ASan/UBSan 检查通过。三次新增全图基线的路径、占用和迭代计数均保持
原有归档结果。协议与证据分别见
[`native_corridor_schema_v1.json`](experiments/native_corridor_schema_v1.json) 和
[`native_corridor_progress_20261013.json`](experiments/native_corridor_progress_20261013.json)。

```bash
python3 tools/run_native_cohort.py --search-run work/u280_native_search_v2_20261013 \
  --independent-run work/u280_native_search_v2_independent_20261013 \
  --quotient-run work/u280_native_quotient_v1_20261013 \
  --router work/native_corridor_build_20261013/dieroute_native_cohort \
  --corridor-attempts 8 --corridor-reentry --corridor-cost-bound \
  --shadow-sync-searches 3 --repeats 5 --output work/new_corridor_run
python3 tools/audit_native_cohort.py --run work/new_corridor_run \
  --output work/new_corridor_cohort_audit
python3 tools/audit_native_corridor.py --run work/new_corridor_run \
  --cohort-audit work/new_corridor_cohort_audit --output work/new_corridor_protocol_audit
```

## 多出口完整候选比较

新增 `--corridor-candidates N`，默认值 1 保持首个可行方案策略。大于 1 时，
完成一个非本地方案后排除其最后一个出口，再按现有排序生成新方案，最后按
完整增量分支代价及固定平局规则选择。`--corridor-attempts` 仍限制全部尝试，
失败和代价剪枝也消耗这个预算；N 只限制完成方案数。多跳通道的上游出口仍是
启发式选择，因此不保证枚举全部通道。启用新入口比较时，本地延伸先参与比较，
但不占非本地候选名额。

同一开发工作负载的方案预先记录在
[`native_portal_comparison_plan_v1.json`](experiments/native_portal_comparison_plan_v1.json)。
以下命令关闭新入口比较，单独检验多出口比较；每次使用新的输出目录。

```bash
python3 tools/run_native_cohort.py --search-run work/u280_native_search_v2_20261013 \
  --independent-run work/u280_native_search_v2_independent_20261013 \
  --quotient-run work/u280_native_quotient_v1_20261013 \
  --router work/native_corridor_build_20261013/dieroute_native_cohort \
  --corridor-attempts 8 --corridor-candidates 8 --corridor-cost-bound \
  --repeats 5 --output work/new_portal_comparison
```

默认兼容、全局尝试上限、完成候选上限、等代价选择、落选/剪枝释放均有测试。
另有 500 组固定种子、四出口且可穷举的图，对比独立完整路径最优解；这个最优性
结论只适用于所测的可穷举拓扑，不扩展为真实多跳图的全局最优声明。

四种新增配置均完成五次重复和独立 PIP/权威状态重建。默认配置的路径、
占用及迭代计数与此前归档一致；8 候选加 shadow 周期 3 后最终路由和占用
仍一致，每次有 18 次重放。主要结果如下：

| 配置 | 树 PIP 数 | 详细搜索展开节点 | 商图展开分组 |
|---|---:|---:|---:|
| flat 基线 | 2,528 | 7,841,282 | 147,981,897 |
| 1 候选 | 2,745 | 8,217,524 | 163,621,135 |
| 最多 2 个完整候选 | 2,694 | 13,117,072 | 193,060,833 |
| 最多 8 个完整候选 | 2,655 | 27,142,251 | 305,127,511 |
| 8 候选 + shadow 周期 3 | 2,655 | 43,386,493 | 359,952,318 |

8 候选比 1 候选少 90 个 PIP（3.28%），但仍比 flat 多 127 个
（5.02%），详细搜索展开量为 1 候选的 3.30 倍。选中 SLL 均为 36。
这验证了首个可行出口策略仍有改进空间，也暴露了逐个完整候选搜索的开销。
**质量门槛仍未通过**；本轮未进行新树的 DCP/STA/DRC 验收，不能将 PIP 数
当作物理线长、将展开次数当作延迟或宣称硬件加速。31 项 CTest（含上述
500 组随机用例）及两个受影响目标的 ASan/UBSan 检查通过。结果和证据见
[`native_portal_progress_20261013.json`](experiments/native_portal_progress_20261013.json)
和 [`summary.csv`](work/native_portal_comparison_v1_20261013/summary.csv)。

## 固定 die 顺序的联合出口搜索

`--corridor-joint-portals` 在固定简单 die 顺序上一次搜索全部合法出口。内部
跨 SLR 节点只能从前一个 die 进入、从后一个 die 离开；同时验证原始 PIP 的
物理 SLR。跨 die 转换发生在同一个电气节点内，不增加虚构边或重复占用。
边界 sink 可以直接完成最后一次零 hop 转换，不要求在目标 die 上再有出边。
完整路径发现后才记录其候选预留集合，失败发现不创建预留；只有最终接纳分支
修改权威状态。联合模式不进行几何候选枚举。

**范围限制：** 可用边界节点至多属于两个 SLR，其他拓扑明确报错。最短路结论
仅适用于固定 die 顺序及完成的搜索，不包含其他 die 顺序、die 重入或全局共享树
最优性。失败仍可执行有计数的全图回退；它不是分布式容量授予或硬件实现。

四种新增配置各重复五次并通过独立 PIP、完整代价、权威状态及 shadow 重放审计。
联合搜索、重入比较及 shadow 组合的最终树、路径和占用，均与 flat 基线逐字节
一致，选中树为 2528 个 PIP、36 个 SLL。所有 298 条最终路径都没有 die 重入
或将内部跨 SLR 节点当作同 die 连线的情形。

| 配置 | 树 PIP 数 | 详细搜索展开节点 | 商图展开分组 |
|---|---:|---:|---:|
| flat 基线 | 2,528 | 7,841,282 | 147,981,897 |
| 逐个比较最多 8 个候选 | 2,655 | 27,142,251 | 305,127,511 |
| 固定顺序联合搜索 | 2,528 | 9,576,624 | 149,611,787 |
| 联合搜索 + 重入比较 | 2,528 | 9,584,211 | 152,294,784 |
| 联合搜索 + 重入 + shadow 周期 3 | 2,528 | 10,811,779 | 154,343,952 |

联合搜索相对 8 候选减少 64.72% 的详细展开和 50.97% 的商图展开，
但详细展开仍比 flat 多 22.13%。每次重复有两次调用执行回退后仍报预算耗尽，
随后随共享树增长在受限搜索中完成；本组没有通过全图回退成功接纳的分支。
重入比较没有发现更优候选；shadow 周期 3 每次有 4 次重放，最终结果仍一致。

32 项 CTest 与三个受影响目标的 ASan/UBSan 检查通过。新增 500 组三 die
图与独立物理路径穷举对照（262 可达、238 不可达）；另在已有 500 组双 die
完整通道用例中验证了联合搜索代价。路径分类也有包含同 die 边界用法的用例。

**联合物理 QoR 和硬件验收仍未完成。** 这里的相等对象是初始 flat 重路由树，
不是后来恢复 hold 裕量的修复树；本轮没有新 DCP/STA/DRC 验收。展开次数不代表
延迟或硬件加速比。算法协议、预定对照与证据见
[`native_joint_schema_v1.json`](experiments/native_joint_schema_v1.json)、
[`native_joint_comparison_plan_v1.json`](experiments/native_joint_comparison_plan_v1.json) 和
[`native_joint_progress_20261013.json`](experiments/native_joint_progress_20261013.json)。

```bash
python3 tools/run_native_cohort.py --search-run work/u280_native_search_v2_20261013 \
  --independent-run work/u280_native_search_v2_independent_20261013 \
  --quotient-run work/u280_native_quotient_v1_20261013 \
  --router work/native_joint_build_20261013/dieroute_native_cohort \
  --corridor-attempts 8 --corridor-joint-portals \
  --repeats 5 --output work/new_joint_corridor
```

## 预算延后与停滞补救

`--corridor-defer-budget` 只适用于联合搜索。没有完整候选且受限搜索触及资源
预算时，先返回 `budget_exhausted`，让后续 sink 有机会增长共享树。只要树增长，
便按原定顺序重试未完成任务；如果一轮没有增长且仍有预算延后，则只切换一次
到全图补救阶段，直接搜索未完成任务，不重复受限搜索。补救阶段继续以树增长
作为重试条件。其他搜索失败仍立即回退；已有完整候选也不会被延后。默认策略
保持不变。预算耗尽不等于不可达，补救同样可能在给定预算内失败。

每个候选尝试现在单独记录搜索状态及展开/边访问数；受限联合搜索、分段局部
搜索和全图搜索的工作量严格合计为总量，包括异常前已经发生的工作。
`cohort_passes.csv` 记录每轮树大小、失败任务、预算延后、补救状态和继续条件。
独立核验器从重建的权威状态推导任务顺序、已共享 sink、重试及补救切换，
而不只相信日志中的阶段标签。shadow 过期时先重放，再用最终有效结果决定延后。

| 配置 | 详细搜索展开节点 | 其中全图展开 | 商图展开分组 |
|---|---:|---:|---:|
| flat 基线 | 7,841,282 | 全部 | 147,981,897 |
| 联合搜索，立即回退 | 9,576,624 | 1,745,654 | 149,611,787 |
| 联合搜索，预算延后 | 7,830,970 | 0 | 147,981,897 |
| 延后 + 重入比较 | 7,838,557 | 0 | 150,664,894 |
| 延后 + 重入 + shadow 周期 3 | 9,066,125 | 0 | 152,714,062 |

四种新增配置各重复五次，均通过 PIP、完整代价、权威状态及调度审计。最终
树、路径和占用仍与 flat 逐字节一致（2528 个 PIP、36 个 SLL）。立即回退与
延后配置的完整受限搜索日志也逐字节一致；减少的 1,745,654 次展开全部来自被省去的
全图搜索，总展开量减少 18.23%。新展开量比 flat 少 0.132%，商图工作量
与 flat 完全相同。这些是软件工作计数，不构成延迟、HBM 流量或硬件加速证据。

每次重复有两次预算延后，都随树增长恢复，因此真实开发集没有进入全图补救。
专门用例验证了停滞后必须靠补救才能找到合法路径，以及补救仍耗尽预算时正常
终止；篡改阶段、失败状态或工作量会被核验器拒绝。32 项 CTest、两个受影响
目标的 ASan/UBSan 检查及异常部分工作量检查均通过。

**完整研究仍未完成。** 本轮未做新的物理 QoR 或 DCP/STA/DRC 验收，尚需
把当前中央权威状态和源端观察副本落实为真正的 die-local 单 owner 数据面。
协议、预定对照和证据见
[`native_defer_schema_v1.json`](experiments/native_defer_schema_v1.json)、
[`native_defer_comparison_plan_v1.json`](experiments/native_defer_comparison_plan_v1.json) 和
[`native_defer_progress_20261013.json`](experiments/native_defer_progress_20261013.json)。

```bash
python3 tools/run_native_cohort.py --search-run work/u280_native_search_v2_20261013 \
  --independent-run work/u280_native_search_v2_independent_20261013 \
  --quotient-run work/u280_native_quotient_v1_20261013 \
  --router work/native_defer_build_20261013/dieroute_native_cohort \
  --corridor-attempts 8 --corridor-joint-portals --corridor-defer-budget \
  --repeats 5 --output work/new_budget_deferred_run
```

## 单 owner 权威状态分区（2026-10-13）

`NativeRouteState` 现在可将占用 net 集合、history 和 version 实际存入最多八个
独立 owner 分区。每个电气节点只保留一份权威记录；owner 是完整 SLR membership
的最低置位，不改变拓扑 membership，也不复制共享 SLL 的容量。默认单 owner
保留为对照，`--owner-partition` 启用分区。

跨分区接纳先完成全部路径、版本和 owner 检查及分配，再转移预分配节点并发布
路由树；rip-up 和 history 协商同样先检查所有分区。空占用记录保留历史和版本。
这提供串行逻辑原子性，尚不是并发分布式提交。全局导出以最多八路迭代器归并
保持原来的节点顺序，不维护另一份中央权威表。

复制、交换、显式检查点恢复和时序修复均携带分区布局。时序控制器拒绝候选
布局发生变化；独立反馈程序可接收 owner 标志，导入时核验 owner 清单，
批运行器从路由 manifest 传递此标志。漏传标志而输入包含非零 owner 时明确
拒绝，避免静默合并分区。`owner_usage.csv` 直接枚举实际分区，并由 Python
独立核对原生 membership、占用、history、version 和空记录。

固定 70-net 开发集完成集中式对照、三分区、三分区加 reentry/shadow3 三组，
各五次重复。集中式与分区式的已有 CSV 日志逐字节一致，三组也分别复现上一轮
对应配置的全部 CSV 日志。最终均为 2,528 PIPs、36 SLL；分区改变状态存储，
没有改变本轮路径选择或搜索工作量。

| owner | 权威记录（含空记录） | 边界记录 |
|---|---:|---:|
| 0 | 983 | 19 |
| 1 | 1,062 | 17 |
| 2 | 564 | 0 |

33 项 CTest、六个相关目标的 ASan/UBSan 检查和 1,000 次随机跨 owner 操作
对照覆盖了唯一存储、末端分区失败无副作用、复制/恢复，以及修复流程。
独立反馈 host 的 14 个案例包含遗漏分区标志、错误 owner 和缺失清单的拒绝。
使用已冻结的原生时序观测重放四种流程后，14 份检查点的 owner 清单均通过
独立审计，canonical 状态与决策逐字节复现历史结果；hold20 仍恢复相同五个
net。该重放验证状态管理，没有重新测量原生时序。完整结果与验收边界见
[`native_owner_progress_20261013.json`](experiments/native_owner_progress_20261013.json)，
协议见 [`native_owner_schema_v1.json`](experiments/native_owner_schema_v1.json)。

```bash
python3 tools/run_native_cohort.py --search-run work/u280_native_search_v2_20261013 \
  --independent-run work/u280_native_search_v2_independent_20261013 \
  --quotient-run work/u280_native_quotient_v1_20261013 \
  --router work/native_owner_build_20261013/dieroute_native_cohort \
  --corridor-attempts 8 --corridor-joint-portals --corridor-defer-budget \
  --owner-partition --repeats 5 --output work/new_owner_partition_run
```

搜索和提交仍由串行控制器驱动，shadow 仍使用源端 observer。分阶段本地 worker、
真实 HBM bank 映射、并发同步和任务迁移尚未实现。本轮不产生新的原生物理
签核或板上性能结果；现有 QoR、代表性工作负载和硬件验收门槛保持开放。

## 各 die 的搜索队列与边界访问（2026-10-13）

`--die-workers` 将联合 corridor 搜索的标签表和优先队列实际分到各 die。
资源 owner 仍按完整 membership 的最低置位确定；搜索标签则放在该节点
下一条物理 PIP 所在的 die。边界节点在进入下一阶段时把候选标签交给下一
worker，不新增电气节点、PIP、跳数或代价。根使用首阶段，终端使用指定的
目标 die。各队列头由确定性仲裁器选择全局最小项，因此保持原搜索的 tie-break。
标签和扩展预算作用于所有 worker 的总和。

`NativeDieAccess` 拒绝访问不属于当前 worker 的内部节点，并检查调用方的
membership 与不可变拓扑完全相同。本地资源由该 owner 读取；非 owner 的
边界访问经过 owner 摘要服务，只返回占用数量、history、version，不复制可写
net 集合。摘要在一次候选阶段内保持不变，提交前检查所有边界读取，包括
未出现在最终路径上的读取。控制器 generation 还保护本地读取和检查点替换。
失败的状态更新不会改变 generation；有效更新保守地使旧阶段失效。

这是串行 worker 调度参考，未允许其他线程同时修改状态。新模式与旧的源端
observer/shadow 周期实验分开，要求 `--shadow-sync-searches 0`。当前摘要按需
获取，尚不跨候选持久缓存。预算补救中的全图搜索仍是显式、单独计数的
控制器回退，不能把它算成 die-local 搜索。

固定 70-net 开发集的集中式对照、worker 模式和 worker 加 reentry 比较三组
均运行五次。worker 模式保留对照的路径、占用、history、版本及原有工作日志。
首配置每次 7,830,970 次扩展分布如下：

| 搜索 worker | 扩展节点数 |
|---|---:|
| die 0 | 557,280 |
| die 1 | 4,467,581 |
| die 2 | 2,806,109 |

每次还有 39,120 次逻辑队列转移、37,697 次边界摘要请求及同数量的验证请求。
这些包含未选中的搜索候选；队列转移仅统计成功入队，不覆盖被拒绝的跨 worker
标签探测。它们不能当作最终物理 SLL 使用量或实测互连字节数。
最终路由仍是 2,528 PIPs、36 SLL。工作量偏向 die 1，为后续 PE/HBM 分配和
迁移实验提供依据；目前没有并行耗时或加速比结论。

验证包括 34 项 CTest、七项相关 ASan/UBSan 检查、3,000 个独立稠密搜索对照、
1,500 个引导搜索对照，以及全局预算、三 die 反向穿越、非路径边界变化、
本地状态变化、ABA、检查点替换和异常部分工作计数。独立 Python 审计重建
权威状态，核对每条已记录请求的 owner/摘要和各 worker 工作量守恒；它不
重新执行整个搜索，搜索顺序由独立算法测试验证。

协议与实验记录：[`native_worker_schema_v1.json`](experiments/native_worker_schema_v1.json)、
[`native_worker_progress_20261013.json`](experiments/native_worker_progress_20261013.json)。
新日志为 `worker_queues.csv`、`worker_reads.csv`、`worker_access.csv`。

```bash
python3 tools/run_native_cohort.py --search-run work/u280_native_search_v2_20261013 \
  --independent-run work/u280_native_search_v2_independent_20261013 \
  --quotient-run work/u280_native_quotient_v1_20261013 \
  --router work/native_worker_build_20261013/dieroute_native_cohort \
  --corridor-attempts 8 --corridor-joint-portals --corridor-defer-budget \
  --owner-partition --die-workers --repeats 5 --output work/new_die_worker_run
```

并发提交/重放、持久 worker shadow 发布策略、实际 HBM 传输和任务迁移仍未完成，
本轮也没有新的原生物理签核或板上结果。

## 跨 die 标签请求与响应（2026-10-13）

`SparseLabelWorker` 现在独占标签读写与入队。跨 worker 探测和更新经过固定
64 字节 little-endian 请求/响应，携带搜索 epoch、请求 ID 和标签版本。
重复或延迟更新通过版本检查拒绝，旧 epoch 不改变新工作区；新标签必须取得
串行协调器的全局额度。成功路径的回溯也通过报文读取标签，包括 attachment
根。全局队列头仲裁仍串行，暂未引入异步传输或并发容量授予。

`worker_packets.bin` 保存实际编码后的请求和响应；每条 128 字节归档记录中，
前 64 字节是实验定位信息，后 64 字节才是协议载荷。共享文件头包含架构
fingerprint 和 CRC64。`worker_transport.csv` 按候选与接收方统计探测、更新、
接受、拒绝和回溯。种子分发、队列头仲裁、资源权威摘要走其他通道，因此
这些字节数仅覆盖标签协议，不能称为加速器总流量或物理互连实测流量。

三组固定 70-net/298-connection 开发实验各重复五次，全部原有 CSV 日志
与对应旧 worker 实验逐字节相同；最终仍为 2,528 PIPs、36 SLL。独立审计核对
报文配对、接收方归属、内部边界标签的版本演化、额度拒绝和完整物理回溯。
跨重复仅归一化搜索 epoch 的起点，其余报文字节和相对 epoch 必须一致。

| 每次重复的标签协议计数 | worker | worker + reentry |
|---|---:|---:|
| 探测请求 | 39,120 | 39,128 |
| 更新请求及成功确认 | 39,120 | 39,125 |
| 回溯请求 | 3,047 | 3,047 |
| 请求与响应报文总数 | 162,574 | 162,600 |
| 64 字节载荷总字节数 | 10,404,736 | 10,406,400 |

该开发集没有 stale/epoch/预算拒绝；重入模式有三个探测没有后续更新。
拒绝语义由独立接收方与额度耗尽测试覆盖，不能把这些单元测试事件算入真实图
流量。35 项 CTest 和八项相关 ASan/UBSan 检查通过；重算 CRC 后的 ACK 标志、
标签版本、回溯代价、更新父节点和请求 ID 篡改均被拒绝。原生物理 QoR、
并发提交/重放、持久 worker shadow、HBM 和任务迁移仍待完成。

协议与证据：[`native_transport_schema_v1.json`](experiments/native_transport_schema_v1.json)、
[`native_transport_progress_20261013.json`](experiments/native_transport_progress_20261013.json)。

## 原生整条 net 的并行事务（2026-10-13）

`dieroute_native_parallel` 在同一不可变权威快照上，让不同 net 的候选搜索
通过真实 CPU 线程重叠执行。每条 net 保留原来的多 sink 共享树增长、预算
延后与全图 rescue 顺序；只在 scratch 状态中试探性更新。所有搜索线程结束后，
协调器按原有首 task ID 顺序验证并提交，冲突 net 在最新状态上重新搜索。

读取集合覆盖每次动态代价查询，包括未占用节点和未进入最终路径的节点，
还覆盖候选门户占用及全部写入节点。验证同时检查完整输入树、资源版本、
history 和 net 集合；无关资源的变化不会使候选失效。整条 net 的所有成功
分支先在当前状态的私有副本中验证、暂存，最后一次交换发布。后续分支异常
不会留下部分提交。协商阶段仍允许中间超用，最终必须零超用。

1、2、4 个 net worker 的配置各运行五次。三组的 selection、最终树、PIP 路径、
connection 状态、权威占用/history/version 和 owner 清单均与此前串行 worker
基线逐字节一致。每轮成功提交的搜索工作量也完全一致；额外投机及重放工作
计入总量，独立审计重建每个窗口的快照、冲突、共享树 pass 与原子发布。

| net worker 数 | 观测到的最大重叠候选数 | 每次重复整网重放次数 | 总扩展节点数 | 被丢弃候选的扩展数 |
|---|---:|---:|---:|---:|
| 1 | 1 | 0 | 7,830,970 | 0 |
| 2 | 2 | 12 | 9,325,128 | 1,494,158 |
| 4 | 4 | 23 | 9,876,447 | 2,045,477 |

线程起止区间证明 CPU 搜索确实重叠；它们不构成隔离的端到端加速比或硬件
性能实验。当前简单窗口划分仍有投机浪费，应据完整读取范围改进任务分组。

新增 `transactions.csv`、`readsets.bin`、`proposals.csv`、`proposal_paths.csv`、
`transaction_passes.csv` 和 `conflicts.csv` 记录初次候选与重放；
`accepted_work.csv` 区分成功提交的工作，`iterations.csv` 包含全部工作。
`execution.csv` 的时间戳不参加重复字节比较，读取集合的 ID/version 仍须一致。

验证覆盖 36 项 CTest、两项包含原生驱动的 ASan/UBSan 测试、TSan 事务组件及
1/2/4-worker 并行驱动对照；包含这些对照的原生驱动脚本共通过 22 个案例。TSan 最初在定时同步测试屏障报错，独立的非路由
最小程序复现了同一现象；改用保留五秒超时的 system-clock 等待接口后通过，
原始失败与复现记录均保留。路由实现和 race 检查没有因此被关闭或更改。

```bash
python3 tools/run_native_cohort.py --search-run work/u280_native_search_v2_20261013 \
  --independent-run work/u280_native_search_v2_independent_20261013 \
  --quotient-run work/u280_native_quotient_v1_20261013 \
  --router work/native_parallel_build_20261013/dieroute_native_parallel \
  --corridor-attempts 8 --corridor-joint-portals --corridor-defer-budget \
  --owner-partition --die-workers --net-workers 4 --repeats 5 \
  --output work/new_parallel_net_run
```

协议与证据：[`native_parallel_schema_v1.json`](experiments/native_parallel_schema_v1.json)、
[`native_parallel_progress_20261013.json`](experiments/native_parallel_progress_20261013.json)。
权威发布仍串行，scratch 状态复制属于 CPU 参考机制。持久 worker shadow
的后续验证见下节；异步 owner 协议、HBM 存储映射、迁移和完整物理 QoR 验收仍未完成。

## 持久 die-worker 边界摘要（2026-10-13）

原生并行驱动现可通过 `--worker-shadow-sync N` 启用跨搜索窗口保留的边界
摘要缓存。每个 CPU net lane 分别维护各 die worker 的订阅表；首次读取发送
64 字节请求并接收 64 字节响应，命中时直接使用缓存值。协调器每 N 个窗口
扫描订阅项，仅发送 occupancy/history/version 已变化的 64 字节更新。

提交前既检查完整快照读取集合，也检查搜索实际消费的全部摘要值，包括没有
进入最终路径的读取。缓存相对输入快照已经过期时也会拒绝候选，刷新对应
lane 后在最新状态重放整条 net。每次重复结束时刷新所有订阅项，尾部更新
计入流量。session 与版本检查覆盖旧运行报文、乱序旧版本和重复更新；相同
版本携带不同值会报错。权威状态回退必须开启新 cache session。

四组固定 70-net/298-connection 开发实验各重复五次。独立审计重建请求/响应、
缓存命中、更新、实际消费值、候选验证和最终缓存状态。最终树、物理路径、
占用/history/version、owner 清单及成功提交工作均与对应无缓存并行基线一致。
每窗口刷新还保持原有候选、读取集合和重放日志逐字节一致。

| 配置 | 每次整网重放 | 总扩展节点数 | 冷读次数 | 命中次数 | 更新报文（含尾部） | 请求/响应/更新载荷字节 |
|---|---:|---:|---:|---:|---:|---:|
| 4 worker，关闭 | 23 | 9,876,447 | 0 | 0 | 0 | 0 |
| 4 worker，每窗口 | 23 | 9,876,447 | 20,013 | 24,834 | 107 | 2,568,512 |
| 4 worker，每 3 窗口 | 25 | 11,344,990 | 20,013 | 31,082 | 102 | 2,568,192 |
| 1 worker，每 3 窗口 | 4 | 9,212,405 | 8,827 | 35,539 | 41 | 1,132,480 |

4-worker 的刷新周期从 1 增至 3，仅少 5 条更新消息；包含冷读请求/响应及
最终刷新后的总摘要载荷降低 **0.0125%**，总扩展节点数增加 **14.87%**。
订阅扫描则从 305,217 次降至 179,560 次；尚无隔离的端到端测量
可判断扫描节省与搜索增量的综合影响，此开发集不足以支持更改默认配置。
单 worker 的延迟刷新也产生额外
重放，说明缓存自身过期可独立于并行 net 冲突触发验证失败。

新增 `worker_shadow_messages.bin` 保存 64 字节协议载荷和独立记录元数据；
四份 `persistent_shadow_*.csv` 保存实际读取、验证、路径代价来源及发布记录。
跨重复只归一化 session/重复号，其余报文字节必须一致。报文计数包含冷读
请求、响应、变化更新和最终尾部；不包含验证协议流量或物理链路开销。

37 项 CTest、三项 ASan/UBSan 测试、两项 TSan 组件测试，以及使用 TSan
并行驱动的 23-case 主机对照脚本通过。覆盖新快照配旧缓存、非路径过期读取、
真实跨 die 路径上的过期代价与刷新重放；篡改报文值并重算 CRC 仍被独立
审计拒绝。最初测试使用的同 die fixture 没有远端读取，已改为真实跨 die
fixture 检验协议，保留诊断记录。

这是搜索线程全部结束后发布更新的 CPU 参考模型；缓存订阅扫描、权威读取
与提交验证仍由主机实现。尚未证明异步网络一致性、HBM 带宽/延迟、硬件加速
或新物理 QoR。新配置沿用 `--net-workers` 并添加 `--worker-shadow-sync 1`
或 `3`；省略该参数即关闭。

协议与证据：[`native_persistent_shadow_schema_v1.json`](experiments/native_persistent_shadow_schema_v1.json)、
[`native_persistent_shadow_progress_20261013.json`](experiments/native_persistent_shadow_progress_20261013.json)。

## HBM 摘要端点与三 CU 硬件仿真（2026-10-13）

`src/summary_hbm.cpp` 将边界摘要协议落实为可综合的存储与队列端点。
它支持 owner 摘要安装、读取、比较验证，以及 worker 缓存接收与查询；
完整 net 集合、占用计算和整网原子提交仍由 CPU 控制层负责。owner 安装需要
期望版本，并验证完整 SLR membership；相同版本不同值、旧 session、旧版本、
错误角色/地址和保留位均得到明确状态。

请求与响应使用 HBM 环形队列。单条命令由 64 字节原协议报文加 64 字节
描述符组成；响应含报文与执行回执。只有有响应空间时才消费请求并修改状态。
票号不回绕，容量/可用数量与运行步数均受检查。调用期间缓冲由内核独占，
完成后再交还控制器；尚无独立运行的跨 CU 网络或整网硬件提交。

HLS 2022.2 在 XCU280 上完成 C 仿真、综合、15 次调用的 Verilog 协同仿真与
XO 导出。接口审计核对了四个 512 位 AXI master（请求、owner、shadow、响应）
和一个 64 位拓扑端口，owner/cache 存储分别连接独立接口。

| HLS 组件指标 | 最终结果 |
|---|---:|
| 目标周期 / 时钟不确定度 | 4.000 / 1.080 ns |
| 报告估计周期 | 2.920 ns |
| LUT / FF / DSP | 25,192 / 27,252 / 3 |
| BRAM / URAM | 0 / 0 |

首版 AXI 缓冲配置估计 44,948 LUT，容量检查路径超过有效预算 0.063 ns。
给启动检查增加寄存级、将顺序端点的 AXI outstanding/burst 容量缩至 2 后，
功能验证保持通过，估计时序告警消除。以上是 HLS 估计；平台布线后时序尚待验证。

真实图使用全部 46,848 个共享边界节点建立紧凑 slot 表。三组缓存配置各重复
五次，共 **245,515 次接收和同量查询** 与既有 CPU 接收方逐条一致，最终
缓存也由独立 Python 审计与完整尾部刷新后的权威表比较。4-lane 配置每个
worker 的完整槽位缓存占 11,993,088 字节。该大图重放运行于 C 模型；
RTL/平台执行使用覆盖版本、会话、背压、恢复及错误输入的定向小型测试。

`config/summary_hbm_u280.cfg` 将三个 CU 的六个指针参数分别绑定到
HBM 0–4、8–12、16–20。`v++ --target hw_emu` 链接成功，xclbin 的 18 条
指针连接全部与配置匹配。平台元数据确认 HBM 端口宽度为 256 位且全部位于
物理 SLR0；逻辑 die、CU 放置与 HBM bank 分组需要分别评估。
仿真存储的类型枚举为通用 DRAM/DDR，审计同时核对平台 HBM 标签、32 个通道、
每通道 256 MiB、地址不重叠及实际连接，保留了初次枚举假设错误的诊断。

XRT 2.14.354 主机将同一测试程序的内核调用替换为实际 CU 调用，未链接 CPU
内核实现。设备缓冲跨调用复用；15 次调用全部通过，其中
**12 次无需重新上传 owner/cache 状态**。三个 CU 的实际 group ID 与配置一致，
仿真器正常退出。该 hw_emu xclbin 的时钟元数据为平台默认 300 MHz；
这没有验证物理 300 MHz 时序，也不能代替 4 ns HLS 约束下的完整平台实现。

38 项 CTest、端点 ASan/UBSan 与真实延迟刷新轨迹的 sanitizer 重放通过。
原始失败记录包括 HLS 项目路径/聚合参数、XRT 编译依赖，以及仿真启动缺少
`USER`；最终启动仅在子进程补入实际用户名。当前仍无物理 Xilinx 卡。

协议与证据：[`summary_hbm_schema_v1.json`](experiments/summary_hbm_schema_v1.json)、
[`summary_hbm_progress_20261013.json`](experiments/summary_hbm_progress_20261013.json)。
完整原生 search/commit 接入、异步一致性、自动发布/调度、迁移消融、布线后
平台时序、完整物理 QoR 和板上测量继续开放。

## 原生搜索接入 HBM 摘要端点（2026-10-13）

`--summary-hbm` 将持久摘要后端替换为同一个可综合端点：冷读、命中值、刷新
读取及提交前的实际消费值验证均来自端点响应。CPU 保留订阅键和发布记账，
不再使用主机 worker 值缓存供应搜索代价；完整 net 集合、搜索前沿与整网原子
提交仍在 CPU。端点 owner 表镜像所选 net 的权威状态；未选 net 的 footprint
继续由原生访问保护冻结。

控制器在全部搜索线程结束后的边界发布 owner 更新，再验证候选和执行固定序
提交。每个 actor/CU 有独立环形队列票号，每个 CU 的调用由互斥锁串行化；
搜索阶段各 lane 的缓存独立，因此日志可按 lane 顺序确定性线性化。这不是
实际设备事件时序，也没有证明异步生产者/消费者的内存一致性。

固定 70-net / 298-connection 开发集使用全部 46,848 个共享边界 slot。
4-worker 周期 1、4-worker 周期 3、1-worker 周期 3 各运行五次，
每组 **19 份原有 CSV/读集合/64 字节摘要报文全部与对应旧后端逐字节一致**。
新增日志记录命令、描述符、回复、回执与完成状态；独立 Python 重放同时绑定
实际搜索读取、陈旧判定、CPU 提交边界及最终 owner/cache 表。

每次重复的端点操作数如下（均为 C 模型功能计数）：

| 操作 | 4 worker / 周期 1 | 4 worker / 周期 3 | 1 worker / 周期 3 |
|---|---:|---:|---:|
| owner 安装 | 46,891 | 46,891 | 46,891 |
| owner 读取 | 325,230 | 199,573 | 196,298 |
| 缓存接收 | 20,120 | 20,115 | 8,868 |
| 缓存查询 | 330,051 | 210,642 | 223,010 |
| 读取值验证 | 44,847 | 51,095 | 44,366 |

三组共记录 9,074,440 条操作；各组除重复号/session 外，完整命令轨迹跨五次
重复一致。当前每次调用只处理一条命令，刷新仍需 CPU 遍历订阅；该接入证明
语义闭合，没有建立吞吐优势。进一步的批处理和自动调度需要单独验证。

XRT 驱动只链接硬件适配器，不链接 CPU 内核实现。两个三 die 小型原生路由
测试分别执行 66 次 CU 调用，共 **132 次**；所有确定性输出与 C 模型完全一致，
每次调用均无需重新上传 owner/cache 状态。沿用已核验的三 CU hw_emu xclbin，
综合内核源码及 ABI 未改变。这个 XRT 适配器目前限于 16 个 slot、4 个 lane、
3 个 CU；真实大图验证运行于 C 模型。没有新增物理布局/时序或板上结果。

39 项 CTest 通过；新增实际旧摘要代价、失效验证、原子拒绝与刷新重算的组件
测试，ASan/UBSan 通过，双线程同 CU/独立 lane 测试在 TSan 下通过。
24-case 主机测试覆盖原有后端与新端点后端。篡改命令、响应、回执并重算 CRC
会被拒绝；保持端点状态转换合法、但谎报 owner 安装的提交边界，也被独立
控制器重放拒绝。首轮测试发现 fixture 路径变量被覆盖，修复后全部通过，
失败日志保留。

协议与证据：[`native_summary_hbm_schema_v1.json`](experiments/native_summary_hbm_schema_v1.json)、
[`native_summary_hbm_progress_20261013.json`](experiments/native_summary_hbm_progress_20261013.json)。
研究仍需整网硬件权威/提交、自动发布和异步队列、映射/迁移消融、代表性
全设计物理 QoR、平台布线后时序与板上测量。

## Owner 订阅与按变化发布引擎（2026-10-14）

`src/owner_publish_hbm.cpp` 增加原子 subscribe+fetch：owner 返回当前值时登记
worker/lane，后续 owner 安装将相应订阅者标记为待发布。每个 slot 最多在
待发布队列出现一次；多次更新合并为最新版本，支持按 worker/lane 选择性
发送。只有更新成功写入输出队列后才清除对应待发布位，满队列、预算限制、
旧 session 和票号耗尽均有定向测试。调用期间仍采用独占缓冲交接；尚无
并发 DMA 或中途崩溃原子性保证。

此前的 70-net / 298-connection 三组已审计命令，各重复五次，重新由新 owner
引擎及原接收端执行。全部读取/验证响应、变化发布和最终 owner/cache 表与
源记录一致；独立 Python 状态机另行重建订阅位图、唯一待发布队列、合并、
筛选、票号及会话。下表为每次重复的功能计数：

| 配置 | 移除的扫描查询 | 待发布队列检查 | 输出变化更新 | 替代后全部端点调用 |
|---|---:|---:|---:|---:|
| 4 worker / 周期 1 | 610,434 | 285 | 107 | 156,981 |
| 4 worker / 周期 3 | 359,120 | 299 | 102 | 169,363 |
| 1 worker / 周期 3 | 374,942 | 41 | 41 | 144,601 |

这是**既有搜索命令的替代重放**，并未用新发布器重新运行在线路由。CPU 仍
提交 owner 值并分发输出；重放分发层仅重编排 worker/node 顺序和传输序号，
硬件输出的占用、历史、版本均原样保留并与源记录核对。计数减少不能直接
换算为吞吐、HBM 实际流量、板上加速或新的物理 QoR。

发布器完成 40 次调用的 HLS C/RTL 验证，最终 HLS 估计周期 2.920 ns
（4 ns 目标、1.080 ns 不确定度），估计 50,845 LUT、42,144 FF，
DSP/BRAM/URAM 为零。首版功能通过但估计周期 5.712 ns；关闭不适合状态依赖
的自动流水化、给订阅掩码计算增加寄存级后消除时序预算告警。

初次六 CU 链接超过平台 master 连接数限制。将发布器请求/回复合并到 traffic，
拓扑/待发布队列合并到 index，并保留 owner、订阅表与发布输出三个独立端口后，
六 CU 共 30 个 master；hw_emu 链接核对 **45 条指针连接、21 个 HBM bank**。
接口修改前后的主机预处理源码与重建后的 C 模型重放程序逐字节相同，功能
重放证据沿用并保留了原源码及等价性记录。hw_emu 时钟元数据仍为 300 MHz；这不等于 4 ns HLS 约束下的平台实现，
物理 SLR 放置和布线后时序仍未证明。

联合 XRT 适配器在 owner 与接收端之间复用同一 topology/owner BO；实际加载
新发布器与原接收端，未链接 CPU 内核。定向测试 40 次调用、两个小型命令
重放（各 3 个边界 slot、3 次重复）各 63 次调用，共 **166 次**；两个重放的全部事件/状态输出与 C 模型一致，
且全部调用无需重新上传 owner/订阅/队列/cache 状态。定向故障注入会按测试
要求上传修改过的状态。该适配器限于 16 slot、4 lane、3 die，真实大图仍为
C 模型验证。

41 项 CTest、ASan/UBSan 组件与五重复真实命令重放通过。12 个重算 CRC 后的
语义篡改被独立审计拒绝。失败的时序与端口预算尝试均保留。

协议与证据：[`owner_publish_schema_v1.json`](experiments/owner_publish_schema_v1.json)、
[`owner_publish_progress_20261013.json`](experiments/owner_publish_progress_20261013.json)。
下一步必须将订阅和队列排空接回在线 native 搜索，重跑真实路由及小型 XRT
路由测试；随后继续整网硬件提交、映射/迁移、完整 QoR 和板上门槛。

## 原生在线路由接入 Owner 发布器（2026-10-14）

`--summary-push` 选择后端模式 2，要求启用持久 worker 摘要。搜索的冷读取
原子登记 worker/lane 订阅；owner 更新产生待发布位和唯一 dirty slot；周期、
强制重放前和结束时，主机排空发布队列并通过原接收端更新摘要。刷新不再
逐条扫描订阅值，`publication_scans=0`。主机仍计算搜索、维护 net 集合、执行
整网原子提交、安装已提交 owner tuple 并调度/分发消息。

三组固定 70-net / 298-connection 实验各**重新运行路由五次**，全部 canonical
路由、事务、read-set、实际消费摘要及逻辑消息与原扫描后端一致。publication
表仅扫描次数变为零；新的原始泵调用和更新帧另行记录。每次重复的端点调用
计数如下，包含空队列探测：

| 配置 | 原扫描后端调用 | 在线发布后端调用 | 发布泵调用 | dirty 队列检查 | 变化更新 |
|---|---:|---:|---:|---:|---:|
| 4 worker / 周期 1 | 767,139 | 157,026 | 321 | 212 | 107 |
| 4 worker / 周期 3 | 528,316 | 169,368 | 172 | 216 | 102 |
| 1 worker / 周期 3 | 519,433 | 144,581 | 90 | 41 | 41 |

独立审计重建 owner 值、订阅位图、待发布队列、会话、票号与输出 credits，
逐条关联原始硬件输出、重编排后的逻辑包、接收记录和搜索读取；owner 安装
继续与 CPU 协调器的实际提交边界绑定。最终订阅位图与 receiver cache 完全
对应，待发布位和队列均排空。多 lane 查询在冻结 owner 值的阶段调用，CU
由 mutex 串行保护；不同 lane 的订阅位可交换，记录采用确定的 lane 顺序。
这还不证明自主异步网络或并发 DMA。

42 项 CTest 全部通过；20 个重算 CRC 的语义篡改、2 个端点语义合法但提交
边界错误的记录被拒绝。ASan/UBSan 和 TSan 通过两种后端的过期值成本、拒绝/
重放、并发订阅测试，以及超过输出环容量的多批次合并/tombstone 排空和两组
在线路由。新增压力测试曾错误地复用已占用源节点，修正测试构造后通过，
初次失败日志保留。

两组 3 边界 slot、3 次重复的小型路由直接通过 XRT 执行，使用前阶段六 CU
xclbin，未链接 CPU 内核。每组 69 次 owner/pump 调用、15 次接收端调用，
共 **168 次**；所有确定性产物与 C 模型逐字节一致，所有调用的 owner/订阅/
队列/cache 状态重新上传计数为零。空刷新也真实调用发布器，因此本小例每组
84 次调用多于旧扫描后端的 66 次；真实开发图减少的查询数不能直接换算成
延迟、实际 HBM 流量或板上加速。新旧 synthesizable 内核及 XRT 适配器保持
前阶段已验证版本；没有新增物理时序或板上证据。

协议与结果见 [`native_owner_push_schema_v1.json`](experiments/native_owner_push_schema_v1.json)
和 [`native_owner_push_progress_20261014.json`](experiments/native_owner_push_progress_20261014.json)。
接下来仍需整网硬件权威/原子提交、跨 owner 容量协议、自主或批量传输，以及
完整映射/迁移/拓扑消融、代表性物理 QoR 和板上验收。

为整网硬件提交进行的开发集规模分析显示，单候选最多包含 2,823,767 条读取
（现有 16 B 编码约 45.18 MB），候选路径最多 670 个条目；最终 2,609 个
权威记录不能代表瞬态 staging 容量，也不能作为完整设计规模上界。硬件必须
验证所有路径外、内部和缺省资源读取，不能只检查短路径或边界摘要。
详见 `experiments/native_whole_net_profile_20261014.json` 和
`experiments/native_whole_net_hardware_requirements_v1.json`。

## 整网权威与原子提交组件（2026-10-14）

`dieroute_net_commit_hbm` 将资源占用/历史/版本、精确 net 成员集合和路由树
放入外部存储。每个逻辑 owner 使用独立哈希段，树条目同时链接到 net 和资源；
读集合逐条验证，包含缺省、内部和路径外资源，消费过的摘要还要核对完整 tuple。
提交重新验证 CSR 边、节点权限、attachment、深度及整数代价，将全部分支暂存于
外部 journal；验证、溢出和容量检查全部通过后才发布。失败请求必须保持资源、树、
net 表及控制记录逐字节不变。初始化、根登记、整网提交、保留根的 ripup/free-list
复用、协商历史和 present、只验证与成员查询均已实现；不同槽位不能重复登记
同一 net ID。成功提交直接输出所有变化资源的权威增量。

这仍是串行整网组件。逻辑 owner 段共用一个 authority AXI master，要求独占、
互不重叠的调用缓冲区；不承诺并发 DMA 或断电原子性。协商路由有意允许暂时
overuse，不能替代严格的跨 owner 容量授予协议。在本组件验收时，在线 native 路由仍由 CPU
维护权威状态；后续在线接入见下一节。

36 次定向测试、39 次容量/溢出/损坏链表测试，以及 195 次原生模型对照与长读集
调用通过。长读集合含 **2,823,767 条记录**，最后一条发生冲突时也能完整检查并
原子拒绝。独立回放器按字典集合和树模型重算成功转移、读/摘要冲突及增量，
共核对 270 次实际 ABI 调用，并拒绝 35 种语义篡改。除 conflict 外的错误码分类
由定向 C++ 用例断言，回放器不宣称独立复刻全部畸形输入分类。46 项 CTest 和
三组 ASan/UBSan 检查全部通过。

最终 HLS 组件完成 **75 次 C/RTL 调用**；4 ns 目标扣除 1.080 ns 不确定度后，
估计周期 2.920 ns 满足预算，估计使用 100,316 LUT、79,498 FF、35 DSP，
BRAM/URAM 为零。traffic/authority 为 512-bit，graph 为 64-bit，导出 27 个显式
AXI-Lite 参数。首版 3.779 ns 时序失败通过独立完成写回控制模块修复；检查中
发现的重复 net ID 错误接受已加入回归并修复，两类失败均保留日志。这些为
综合估计及功能仿真，不是布线后时序或板上吞吐。

<!-- net-commit-platform-status:start -->
独立 U280 单 CU 的 hw_emu 链接通过，核对 **15 条指针连接、3 个 HBM bank**。
XRT 的 36 次定向及 39 次边界调用全部通过独立回放，完整记录与 C 模型逐字节
一致。普通流程的 CPU 权威状态覆写计数为零；边界测试显式允许夹具重置和
故障注入，共 32 次权威 BO 上传。另有 6 次实际内核调用验证宿主保护：
对四类权威缓冲区的 4 次 CPU 覆写尝试均在内核启动前拒绝，后续设备查询
确认原状态未变。三组共 **81 次 XRT 内核调用**，均使用设备内核，未链接 CPU
内核实现；限于 12-node 小型夹具，不能扩展解读为真实大图执行。

首轮 XRT 边界测试的有效结果全部正确，但适配器下载了未产生的 delta 尾部，
使 15 帧的无效缓冲区尾部与新夹具不同。改为只下载 completion 声明的有效
增量后，复跑完整 75 次调用并通过逐字节比较；失败记录与诊断均保留。
xclbin 的时钟元数据为 300 MHz，不等于 4 ns HLS 约束下的物理实现或时序证明。
本节单独组件验收时尚未与 owner 发布器/接收端联合链接；当前联合进度见下文。
<!-- net-commit-platform-status:end -->

协议见 [`net_commit_schema_v1.json`](experiments/net_commit_schema_v1.json)，阶段
计划见 [`net_commit_plan_v1.json`](experiments/net_commit_plan_v1.json)，验收与冻结
证据见 [`net_commit_progress_20261014.json`](experiments/net_commit_progress_20261014.json)。后续在线接入
已完成下面的 C 模型验收；联合硬件执行仍待验证。不能将本节组件测试
写成完整 FPGA 路由或物理性能结果。

## Native 在线整网权威接入（2026-10-14，C 模型）

`--net-commit` 将初始化、根登记、候选提交、ripup 和协商全部接入可综合
`dieroute_net_commit_hbm`。搜索读取由内核记录导出的快照，CPU 权威状态只作
独立对照；每个初始及重放候选均真正调用内核，CPU 验证不能提前取消调用。
候选携带完整规范读集合、实际消费的远端摘要和全部成功分支。首次发布投影
内核稀疏状态，此后只将内核生成的边界资源增量原样送入 owner 发布器。

真实 U280 图上，固定 70-net/298-connection 开发集的新运行全部通过：

| 配置 | 重复次数 | 每次整网内核调用 | 与 CPU 权威逐字节一致的输出 |
|---|---:|---:|---:|
| 4 workers，刷新周期 1 | 5 | 174 | 24 |
| 4 workers，刷新周期 3 | 5 | 176 | 24 |
| 1 worker，刷新周期 3 | 5 | 155 | 24 |

共 **2,525 次在线整网调用**。上述 24 项包含路由、完整读集合、事务、逻辑
消息和摘要端点调用；执行时间与模式说明分别记录。独立审计从输入权限、
候选读/摘要/路径重新计算接受或拒绝、成员关系、树、历史/版本及发布增量，
并将发布绑定到确切调用边界。归一化会话身份后，每组五次的完整 ABI/状态
记录和发布记录哈希均一致。最大单次读集合 **2,823,767 条**，没有截断。

四个包含拥塞和跨 die 冲突的小型用例完成 177 次在线调用，拒绝 40 个重新
计算 CRC 的语义篡改样本；48 项 CTest 与在线 ASan/UBSan 验证通过。单次
调用观测峰值包括 16,445 条消费摘要、118 个成功分支和 670 个路径节点。
资源记录峰值 2,609、树池高水位 2,598 仅描述该开发集，不能用作完整设计
容量上界；当前池容量耗尽会明确报错，不能静默退回 CPU 提交。

这些真实大图运行使用 **CPU 上的 C 模型内核**。组件内核源码保持此前完成
HLS/RTL/单 CU XRT 验收的版本，但尚未证明在线 native 路由在联合 FPGA
映像中执行。包含三类 XRT 适配器的主机程序已成功编译；联合连接预算、
全图 HBM 放置、硬件执行、异步调度及物理性能仍须分别验收。

可复现入口为 [`native_net_commit_matrix_v1.json`](experiments/native_net_commit_matrix_v1.json)
中的三组配置，以及 `tools/run_native_cohort.py --net-commit --summary-push`。
ABI 日志格式见 [`native_net_commit_trace_v1.json`](experiments/native_net_commit_trace_v1.json)，
完整命令、审计、比较和源码冻结索引见
[`native_net_commit_progress_20261014.json`](experiments/native_net_commit_progress_20261014.json)。

## 七 CU 联合硬件仿真（2026-10-14，在线验证进行中）

接收端新增可选的共享请求/响应 AXI master，默认接口保持原样；三种配置的
非综合预处理代码逐字节相同。共享版本通过 15 次 C/RTL 调用，4 ns 目标下
估计周期为 2.920 ns，导出四个 master。七 CU 联合 U280 `hw_emu` 链接通过，
独立核对 30 个 kernel master、60 条指针连接和 21 个 HBM bank；六种连接
元数据篡改均被拒绝。这不证明物理布局、布线后时序或板上性能。

第一轮在线 XRT 暴露了适配器重复加载同一映像的问题：仿真器重启后，整网
提交因设备会话丢失而拒绝，运行时清理也报错；失败日志和输入完整保留。
两个适配器现共享唯一设备上下文，并拒绝切换到另一份映像。专门的 XRT
保护测试完成七次调用，拒绝一次映像切换和四类 CPU 权威状态覆写，后续
设备查询确认原状态未变，权威 BO 上传计数为零。

内部 die、刷新周期 1 的在线夹具已通过三次重复验收：51 次整网调用、
93 次发布器调用，28 项确定性输出与 C 模型一致，权威状态上传为零。
内部 die、刷新周期 3 的用例也已通过51 次整网/57 次发布器调用验收；
两个跨 die 用例也已通过：周期 1 为 36 次整网、165 次发布器、69 次接收端
调用；周期 3 为 39 次整网、165 次发布器、75 次接收端调用。四组共 801 次
XRT 调用，全部确定性输出与 C 模型一致，源码与日志已冻结。七种实际 XRT 回执篡改均被独立审计拒绝。
真实大图的只读载荷约
3.50 GB，当前权威缓冲区约 59.5 MB、峰值请求及暂存缓冲区约 151.6 MB；
大图候选映像已完成联合链接；三个图参数共享 4 GiB 的 `MBG[16:31]`。
XRT 已实际分配共 3,500,800,632 字节的三个图 BO，地址不重叠，32 个跨 bank
标记读回一致。该分配测试未启动路由内核；真实 policy/CSR 的 3,500,800,632 字节随后完成上传和逐字节读回核对。
使用原生树中的 root 82,754,607、child 82,755,078、PIP 767,946,316，
七次实际内核调用验证了初始化、根登记、错误 PIP 原子拒绝、正确 PIP 提交
及成员查询，非零 CPU 权威上传为零。这是使用完整真实图缓冲区的定向测试；
两组动态尺寸适配器回归已通过并冻结：内部 die 和跨 die 各三次重复，
共 90 次整网调用；设备权威与端点状态上传均为零。70-net 完整在线执行
已提交。前两次启动分别缺少 `XILINX_XRT` 和 `USER`，未进入内核执行；
失败记录保留。第三次加载持久 Vitis/XRT setup 并设置实际 OS 用户后，
已加载唯一映像、配置完整真实图缓冲并开始实际整网 CU 调用，运行与审计
尚未结束。具体状态及证据见
[`native_joint_authority_progress_20261014.json`](experiments/native_joint_authority_progress_20261014.json)。

## 严格 SLL 容量开发配置（2026-10-14）

`NativeCapacityGrants` 只保存临时 distinct-net holds，已提交占用仍由原有
整网权威独占保存。同 net 的多个分支共享容量，整批资源预检后才登记 grant；
释放通过唯一句柄和 net 身份核对，避免旧请求取消新 grant。
严格搜索会过滤被其他 net 占用的电气边界节点，并将被过滤节点也记入完整
读集合；因此未进入最终路径的容量观察仍受版本重放保护。提交前申请完整
边界资源并集，原子提交后或异常时释放 grant。当前实现的共享仲裁区是
所有搜索线程 join 后的 CPU 串行提交阶段，尚不是并发硬件 grant 协议。

原有 70-net 样本的过用节点均为内部资源，不能证明 SLL 争用处理能力。
将每对 die 的种子数固定为 64 后，工作负载覆盖 341 个完整 net、729 个连接，
其中 508 个跨 die。协商基线在四轮内收敛，首轮出现两处实际 SLL 争用，
完整任务/PIP、占用和协议审计通过。严格配置的单次开发运行同样完成所有
连接并在四轮内收敛；完整任务/PIP、占用与协议审计通过，四轮 SLL 过用均为零。相同
CMake Release 构建条件下的五次重复成对实验已完成，独立容量与协议重放通过，
严格配置五次重复中的四轮 SLL 过用均为零。证据见
[`paired verification`](work/native_strict_sll_repeat_pair_v1_20261014/verification.json)。
这些是开发 cohort 的 C 模型结果，不能代替物理联合 QoR、硬件 grant 或板卡性能结论。

严格路由目标为 `dieroute_native_strict_parallel`，驱动为
`tools/run_native_strict_cohort.py`。三个容量/grant/严格搜索专项 CTest 与
ASan/UBSan 检查通过；CMake 与手工构建的跨 die 三次重复通过独立协议
重放，首轮 27 项确定性产物一致。证据与未完成项见
[`native_capacity_grants_progress_20261014.json`](experiments/native_capacity_grants_progress_20261014.json)。

## 后续关键工作

完整快照搜索原型的最新证据见
[`native_snapshot_search_progress_20261014.json`](experiments/native_snapshot_search_progress_20261014.json)，
可引用声明及限制见
[`native_snapshot_claim_matrix_20261014.json`](experiments/native_snapshot_claim_matrix_20261014.json)。
它是单 worker、独占不可变权威状态交接的三 CU 原型，不能代表异步多 worker DieRoute。

| 已验证内容 | 当前证据范围 |
|---|---|
| 完整搜索循环 | 成功/失败定向 RTL、1,000 组随机顶层 C 模型差分；真实跨 die C 模型展开 229,746 节点并逐条核对 862,428 次读取 |
| 真实图搜索与提交 | 42 条 PIP 的 C 模型发布、完整读取集与全部 341 个 net 的树/资源重放；版本冲突和非法 PIP 拒绝时权威状态逐字节不变 |
| 完整树种子与拥塞 | 真实提交后 521 节点树，使用合成的下一目标；C 模型及独立路径审计通过，不能作为原始下一任务结果 |
| 实际 HBM 分配 | 图 HBM[16:31]、缓存 HBM[0:11]、权威 HBM[12]；26 个 BO、35 个指针参数和 94 个跨通道边界标记回读通过 |
| 原生实际搜索 CU | 短连接上传/回读约 3.75 GB 数据，实际 seed/search 各调用一次；路径与读取日志逐字节匹配 C 模型，展开仅两个节点 |

较大跨 die XRT 搜索仍在执行，设备端原生搜索→commit→成员查询闭环排在其后。
冻结三 CU 原型的单 bank 和分 bank `hw` 链接均已完成，300 MHz 目标均未闭合。
分 bank 最终映像的 39 个指针参数及 14 个 AXI master 分组检查通过；工具报告
achieved/DATA 时钟均为 187 MHz，这是映像元数据，尚非实际板上工作频率。
独立打开归档 routed checkpoint 后，300 MHz 约束下 WNS 为 −2.014 ns、
TNS 为 −22733.928 ns，46,868 个 setup 端点失败。包含平台的资源为
249,641 LUT、376,476 FF、422 BRAM、0 URAM、63 DSP；可路由网络均已完成布线。
默认 DRC 有 314 Warning、5 Advisory，无 Error/Critical Warning，但未证明告警豁免。
7 个输入与 3 个输出仍缺少延迟约束。首次逐 CU 探针未返回行；后续按实例路径
核验已确认三个 ap_clk 均使用归档 checkpoint 的 3.333 ns 时钟，见
[`逐 CU 时钟核验`](work/native_snapshot_sharded_cu_clock_probe_20261015/manifest.json)。
归档 checkpoint 与最终 bitstream 的对应关系仍未证明，因此不能据链接成功
或 187 MHz 元数据认定实现签核完成。
证据见 [`独立 checkpoint 报告审计`](work/native_snapshot_sharded_independent_report_audit_20261015/audit.json)。
单 bank 对照中的三个逻辑 owner 分片共享 HBM[12]。新增分 bank 版本的
commit、资源读取和完整搜索通过定向 RTL，并在真实图上通过分离数组的 C 模型差分。
三个 owner BO 分别绑定 HBM[13]、HBM[14]、HBM[15] 的小场景联合 XRT 运行
通过 16 次实际 CU 调用、过期读取拒绝和路径发布，非零权威重上传为零。
证据见 [`banked joint audit`](work/native_snapshot_sharded_joint_xrt_v3_20261014/independent_audit.json)。
它没有证明分 bank 的性能收益或异步并发正确性；原生分 bank 搜索与提交的大图
XRT 验证正在执行。
异步一致性、完整原生 cohort、全部消融、联合 QoR、加速器实现时序和实板性能仍未闭合。

341-net 配置的声明池容量需要约 246 MB 权威状态和 516 MB 请求/暂存载荷，
原映像的单个 256 MiB traffic bank 无法容纳。独立候选映像使用
`HBM[13:15]` 的 768 MiB traffic 组，保留 `HBM[12]` 权威组和
`HBM[16:31]` 图组。实际链接与组拓扑审计通过；15 个 BO 共
4,262,816,232 字节的分配、地址互斥和 56 次合成标记读回通过。
该探针未上传真实图或启动路由 CU，不能据此宣布 341-net XRT 路由完成。
证据见 [`native_341net_platform_progress_20261014.json`](experiments/native_341net_platform_progress_20261014.json)。

`owner_publish_native_sparse_xrt.cpp` 是独立的按行读回适配器：命令阶段只
从设备读取已知 owner/registry 行，接收端按 lane-major 地址读取缓存行；
发布器 pump 与全局错误路径保留整表读回。8 次实际 XRT 保护调用拒绝
5 类 CPU 覆写；使用完整 46,848 槽位目录的另一组 8 次调用验证了高地址
更新、缓存查询和覆写拒绝，状态上传均为零。内部 die 三轮在线等价回归
已通过，跨 die 回归仍在执行；完整 70-net 实验已排在两项前置验证之后。
证据见 [`native_sparse_endpoint_progress_20261014.json`](experiments/native_sparse_endpoint_progress_20261014.json)。

1. 宽代价下的三例时序开发集验证已完成；继续在真实 RR 闭环上优化共享树与增量路由，闭合 WL/CPD
   门槛。已验证基础代价和目标形式会影响质量，但单项改进仍不足以完成研究。
   将已验证的 CPU 乐观预留/版本重放协议落实为 die-local 数据面、
   硬件边界同步与全程计数；不能用软件快照和消息数量代替硬件一致性证据。
2. 将已核验的聚合下界扩展到有可信边下界的真实代价；从已完成的 70-net
   共享树/占用协商与回写扩展到完整设计，改进原生 corridor 的通道排序，将已验证的整条 net 并行候选、固定序提交和持久 worker shadow 推进到异步硬件 owner 协议，
   完成 SLL 容量、原生合法性、时序与线长联合验收。利用已闭合的逻辑负载到
   物理任务映射与新加入的双侧候选验收/恢复机制，进一步优化搜索代价并
   在每次修复后重算原生时序；不能将当前 route/fanout/corner 时延直接当成
   静态可加的 PIP 代价。工作负载 bitstream 已验收；DieRoute 加速器实现仍待完成。
3. 扩展有代表性的真实设计、强并行/完整 timing 基线、全部五组消融与缩放。
4. 将已接入真实 native 路由 C 模型的整网权威，与 owner 发布器和接收端联合
   完成 XRT 硬件执行，补齐异步网络、批量请求、自动发布/调度与物理平台实现。
5. 上板测量端到端性能与能耗，完成论文和可复现实验包。当前环境无已验证
   的物理 U280；不得用 CPU 或 hw_emu 时间代替板上证据。

两次前端失败也保留在 `work/native_*_20261013`：官方 `3d_k4_N4_90nm`
示例上，rca_5bit 的 LUT 输入超限；mult_2x2 触发 VPR 的跨异构层初始布局
断言。成功基线使用上文官方 Stratix IV 双层模型，未修改 VPR 或这些原始架构。

### 2026-10-18：前七个后验配置与硬件候选

后验 12 配置队列的前四个终态原生复核结果汇总在
[`observations.md`](work/width_coverage_first_four_summary_20261018/observations.md)。
四个配置均观察到线长与 CPD 降低，但只涉及两个电路的 seed1；
其中 frisc/cw160 的 CPD 改善仅 1.6 ps。后续两个 elliptic 配置也已完成复核，
前六个结果见 [`audit.json`](work/width_coverage_first_six_summary_20261018/audit.json)。
六个配置均原生合法，线长、CPD 和模型跨层转移数同时下降；仍限于三个电路、
seed1，不能声称全队列通过、统计稳健或物理 SLL 改善。
第七组 apex2/28×22/cw160 也已完成独立复核，三项指标均下降；
第八组 apex2/28×22/cw320 同样原生合法，线长、CPD 与模型跨层转移数均下降。
当前八组汇总见[审计](work/width_coverage_first_eight_summary_20261019/audit.json)，其余四组待复核。

针对上一版未满足 300 MHz 的控制路径，新候选将 generation-counter
更新提取为独立 helper。75 次 C/RTL 仿真通过，仿真总周期由 314460
变为 314495（增加约 0.0111%）。实际硬件 XO 编译完成；
29 个参数、8 个总端口（7 个 AXI master 和 1 个控制端口）与前版一致，
归档主源码逐字节匹配。证据见
[`compiled_XO_review.json`](work/proposal_generation_split_hw_20261018/compiled_XO_review.json)。
完整布局布线及独立复核已完成：300 MHz 保留约束下 WNS 为 -0.773 ns、
TNS 为 -4539.735 ns，18317 个 setup 失败端点；599422 条可布线网络全部完成。
相对上一版 WNS 改善 0.763 ns、TNS 幅度减少 61.7%，仍未时序闭合。
见 [`最终报告对比`](work/proposal_generation_final_timing_comparison_20261018/audit.json)。
DRC 计数采用流程配置的有效严重级别，含继承的 HDPR-5 降级设置；
不代表默认严重级别通过、调整时钟后的签核或上板性能。该候选尚未采纳。

后续发布函数拆分通过 75 次 C/RTL 调用，但 HLS 周期估计恶化至 4.647 ns，
因此保留为负面结果。仅关闭发布循环自动流水化的隔离对照同样通过 75 次调用，
实际 XO 接口及嵌入源码一致，HLS 估计恢复 2.433 ns；仿真总周期增加 2.95%。
该对照完整链接及独立只读审计已完成：599070 条可布线网络全部布通，
但 300 MHz setup 失败，WNS −2.167 ns、TNS −26060.629 ns、49731 个失败端点。
相对父版 WNS 恶化 1.394 ns、失败端点增加 31414 个；不采纳该候选。
见[最终对比](work/publish_record_serial_final_timing_comparison_20261018/audit.json)。
保持、脉宽、总线偏斜通过；DRC 按有效严重级别保留 330 条 Warning 和 5 条 Advisory，
不代表默认严重级别通过、调整时钟后的签核或实卡性能。
实际提交 CU 的独立综合资源相对父版减少 505 LUT、71 个寄存器，BRAM/DSP 不变；
这是 CU 综合阶段结果，不能替代全平台资源、最终时序或性能结论。
见[实际综合复核](work/publish_record_serial_actual_synthesis_review_20261018/audit.json)。
见 [`RTL复核`](work/publish_record_serial_HLS_20261018/independent_RTL_audit.json)
和 [`实际XO复核`](work/publish_record_serial_hw_20261018/compiled_XO_review.json)。

新候选将 ripup 的 predecessor 哨兵判断提取到独立 HLS 函数，保留完整 64 位语义。
75 次 C/RTL 调用通过，实际 XO 的 29 个参数、8 个端口及嵌入源码已核验；
测试夹具总周期为 323805，相对父版 323770 增加约 0.0108%。
实际编译的 HLS 周期估计仍为 2.433 ns，但增加 7747 LUT、7265 FF；
这些是 HLS 估计，不能作为实现后资源或性能结果。
见[RTL 审计](work/ripup_predecessor_helper_HLS_20261018/independent_RTL_audit.json)、
[实际编译对比](work/ripup_predecessor_actual_compile_review_20261018/audit.json)。
物理实现已启动，完成后由已准备的
[只读审计队列](work/ripup_predecessor_helper_postlink_queue_20261018/protocol.json)
检查保留检查点；尚无时序收益结论，未采纳。

前四个配置的最终路由树跨层转移数现已另行重建，按每网 child 节点去重：
apex2/cw160 为 1202→1085，apex2/cw320 为 1291→1109，
frisc/cw160 为 1778→1765，frisc/cw320 为 1774→1751。
因此这四个已复核配置同时观察到线长、CPD 与跨层转移数不劣。
证据见 [`audit.json`](work/width_first_four_crossing_review_20261018/audit.json)。
该计数不是累计 `committed_crossings`，也不是物理 SLL 使用量；
不关闭全队列、统计稳健性或板级门槛。此前汇总中“尚未核验 crossing”
的限制由此新增审计更新，其余范围限制仍然适用。

前四个 parent 的原型成本另见
[`audit.json`](work/width_first_four_routing_costs_20261018/audit.json)：
报告的单次运行时间依次约为 1.43、2.96、1.95、3.87 小时。
上下游搜索占扩展计数约 98.6%–99.6%，表明该原型的搜索工作量仍然很大；
扩展计数不能直接换算为耗时比例。计时包括输入、同步 STA 回调和大部分输出，
不包括预先启动的时序服务初始化、事后原生验证及计时结束后写出的 dispatch 文件。
这些是共享主机上的单次 C++ 原型观测，没有匹配的速度基线，也不是 FPGA 实测。

### 原生参考实现的构建位置与合入边界

2026-10-18 的目标集合优化与原生配对实验使用独立冻结源码：
`work/upstream_target_hash_variant_20261018/source/dieroute`，
配对基线为 `work/rr_remaining_layer_tail_variant_20261015/source/dieroute`。
当前根目录源码尚未包含同一套上游边界搜索，不能把根目录默认构建当作这些实验的复现。
实际构建依赖中，24 个私有源码/头文件有 9 个与当前工作树不同或缺失；
详见 [`audit.json`](work/native_reference_integration_delta_20261018/audit.json)。
这些差异还涉及成本精度、配置接口和控制器，不能整体覆盖已有工作树。
当前候选未采纳，五组实验仍按冻结协议运行。复现该候选应在新的输出目录构建，
避免修改实验所绑定的已生成文件，例如：

```bash
cmake -S work/upstream_target_hash_variant_20261018/source/dieroute \
      -B /tmp/dieroute-upstream-hash-rebuild -DCMAKE_BUILD_TYPE=Release
cmake --build /tmp/dieroute-upstream-hash-rebuild --target dieroute_rr rr_backend_tb -j 2
ctest --test-dir /tmp/dieroute-upstream-hash-rebuild -R '^rr_backend_tb$' --output-on-failure
```

该命令只重建参考程序并运行后端测试，不等同于运行原生配对、验证原生合法性或完成板级评估。

### 目标集合优化：五组原生 CPU 配对终态

五组交替顺序配对、十次运行均完成。410 项路由产物比较一致
（JSON 仅排除运行时间字段），十个持久时序会话均通过来源复核。
完整进程耗时中位降幅为 **8.05%**，五组范围 **7.92%–10.53%**，
包含时序服务启动与退出。证据见
[`audit.json`](work/upstream_hash_five_pair_summary_20261018/audit.json)，
图表见 [`upstream_hash_native_pairs.pdf`](paper/figures/upstream_hash_native_pairs.pdf)。

这是单个 ex5p 开发配置、共享主机且存在缓存及并行工作负载的 CPU 观测；
原先的质量失败保持不变（线长 12255、CPD 10.8661 ns）。
它不证明跨配置性能收益、FPGA 加速或通用决策等价性，候选也尚未合入根目录源码。
运行中的代表性队列继续使用原冻结二进制。

### 后验第五个配置：elliptic/20x16/cw160/seed1

第五个 parent 已完成原生合法性、树状态、时序会话与输入哈希复核。
线长 42513→33882（降低 20.30%），CPD 9.94173→9.87369 ns
（降低 0.684%，68.04 ps），逐网去重的最终跨层转移数 1881→1879。
见 [`audit.json`](work/width_coverage_fifth_parent_evidence_20261018/audit.json)。
第五个结果归档时，五个配置均满足观测到的三项联合不劣。第六个
elliptic/20x16/cw320/seed1 现也完成复核：线长 42284→32562，
CPD 9.90505→9.8666 ns，跨层转移数 1865→1849。
见 [`第六个配置复核`](work/width_coverage_sixth_parent_evidence_20261018/audit.json)。
覆盖仍为三个电路、seed1，其余六个尚无终态复核；不代表统计稳健性、
物理 SLL 或板级加速。

### diffeq：五组 scale256 CPU 配对终态

diffeq 的十次运行均完成，390 项路由产物比较一致，时序会话来源复核通过；
首组直接通过原生验证，后续产物与之相同。完整进程耗时中位降低 **7.49%**，
范围 **4.79%–8.27%**，线长 11584、CPD 7.74031 ns 保持不变。
见 [`independent_case_audit_diffeq.json`](work/upstream_hash_crosscase_pairs_20261018/independent_case_audit_diffeq.json)。
这是原有 scale256 开发配置，单独报告，不与 ex5p/scale1 混合统计；
共享主机和缓存影响仍存在。alu4 的完整终态见下方三电路汇总。

### 三电路 CPU 配对实验终态

ex5p、diffeq、alu4 各完成并复核五对交替顺序实验，共 30 次运行。
各配置内部的路由输出保持一致，完整进程耗时下降中位数分别为 **8.05%、7.49%、7.44%**。
alu4 的下降范围为 **6.65%–10.52%**，线长 10083、CPD 10.2653 ns 保持不变。
首对各自直接通过原生验证，后续输出与首对一致；没有把所有重复都表述为新的原生重放。

见[三电路汇总](work/upstream_hash_three_case_summary_20261018/audit.json)、
[两电路完整审计](work/upstream_hash_crosscase_pairs_20261018/independent_pair_audit.json)和
[配对耗时图](paper/figures/upstream_hash_three_case_pairs.pdf)。
ex5p 使用 scale1，另两例使用 scale256，分别报告，不合并估计；共享主机和缓存影响仍存在。
这是私有 CPU 实现优化，候选未采用，ex5p 原有质量失败仍保留，不代表 FPGA 加速或普遍质量改善。

### 可搬移的 CPU 正确性复现子包

[`dieroute-upstream-hash-cpu-validation.tar.gz`](work/upstream_hash_portable_bundle_20261018/dieroute-upstream-hash-cpu-validation.tar.gz)
包含父版和候选版完整源码快照、独立随机图验证程序及文件哈希，共 844 个文件，约 1.3 MB。
在新目录解包后执行 `python3 reproduce.py`，会重建两版路由器，运行后端测试，
并分别复核 2400 个图、7200 项有界比较的输出。
需要 Linux、C++17 编译器、CMake/CTest 和 Python 3，无须 Vitis/XRT 或原工作区路径。

已完成真实解包重建，验证输出与归档预期一致；两版各九个编译单元的实际依赖仅来自
解包目录和系统 `/usr`。见
[`independent_audit.json`](work/upstream_hash_portable_bundle_20261018/independent_audit.json)。
此子包覆盖 CPU 正确性验证，不复现原生大电路耗时或 FPGA 结果，不代表完整论文制品已完成。
