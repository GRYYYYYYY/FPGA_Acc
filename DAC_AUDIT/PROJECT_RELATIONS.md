# FPGA_Acc 第一阶段关系与证据审计

审计时间：2026-11-10 UTC。源码基准：`b32afa4303a5574dde7171b4ae6e3d07aeb8a06c`。
本次只读取原工程、历史结果和 `/proc`；新增文件仅位于独立 worktree 的 `DAC_AUDIT/`。
没有运行实验、原工程审计脚本、Vivado、HLS 或进程控制命令。历史 handoff 中的继续运行授权不用于本任务。

本报告区分：源码中确有实现、历史终态记录、当前文件哈希匹配、新执行的独立科学验证。
本次完成前三者的定向审查；哈希匹配不等于重新证明算法或重跑原生工具。
`PHASE1_CHECKS.json` 保存每次检查的原路径、迁移后路径、大小、预期与实测 SHA、检查结果。
16 MiB 以上文件仅记录并明确延期，不读波形、不哈希巨型 RR 图；没有将它们记为通过。

## 实际依赖与独立入口

| 工程 | 真实入口及实现 | 工程间关系 | 不应混淆的原型 |
|---|---|---|---|
| PersistRoute | `src/search_hbm.cpp`、`commit_hbm.cpp`；`accelerated_pathfinder.cpp` 控制多轮协商；`host/accelerated_xrt_host.cpp` 管理4个Search CU和Commit CU | VPR转换、原生回写和外部STA是系统闭环的一部分 | 固定容量 `search_kernel` 与 production HBM ABI 不是同一个验收对象 |
| TilePlace | `tools/tileplace_v2.py`生成事务，`run_tileplace_v2.py`负责VPR acceptance/rollback/feedback；完整硬件 `full_color_top` 冻结在work包 | 新cohort的初始时序使用PR paths和proxy delay生成；最终QoR由native VPR给出；不是纯独立于PR的前处理链 | 根CMake/run_hls.tcl只构建早期`tileplace_kernel`，不能证明完整color流水线 |
| RouteCast | `tools/net_shared_capacity_forecast.py`是独立NET搜索复用模块；大量预测/原图证书工具在tools/ | 使用VPR/原图/原生标签；没有已验收的五工程串联部署 | `src/routecast.cpp`/`routecast_kernel`不覆盖后期完整预测与成本管线 |
| DieRoute | `dieroute_rr_backend`链接PR的pathfinder/accelerated_pathfinder/external_timing；`native_*`、owner/summary/net_commit和resident组件有各自入口 | 明确复用PR基础设施；跨die协议和当前resident RTL仍有独立门槛 | `run_hls.tcl`的`dieroute_kernel`不代表后期系统 |
| FusionPAR | `src/joint_state.cpp`、`retained_router.cpp`、`host/joint_host.cpp`；CMake直接编译PR六个生产源文件 | 实际依赖PR C-model；`run_tp_pr_baseline.py`复制且核验封存TP七文件，再做route-only PR；高级TP/RC插件未完成部署 | 早期`fusionpar_kernel`不含完整placement/timing/path修复闭环 |

因此“PR→TP→RC→DR→FP”是研究依赖图，不能画成已经完成并验证的端到端加速器。
FusionPAR目前的整个revision失效、串行发布和affected-net资源并集也不能写成精确最小冲突范围或并行不相交提交。

## PersistRoute

最终tree-seed实现清单为 `experiments/u280_treeseed_hw_2026-08-29.json`，记录source commit `10856a2`。
本次核对search、controller、XRT host和connectivity四个源哈希，全部与基准工作树匹配。
该记录的180 MHz、WNS +0.016 ns、TNS 0证明硬件实现范围；`hw_emu_rerun=false`。
`accelerated_pathfinder_hw_emu_2026-08-26.json`的4-CU功能结果属于早期版本，不能补成最终tree-seed版本的RTL等价证明。
大型xclbin本次仅登记存在、大小和历史SHA，未重新哈希。

六例“corrected”表由旧extended矩阵与spmv weight128结果组合；本次逐例重哈希对应原始`native_validation/validation.json`并读取exit/legality/QoR。
这张表可用于描述已见结果，但不是统一参数、统一来源已闭合的冻结论文主矩阵：spmv seed权重128，其余0。

| 案例 | WL变化 | CPD变化 | Balanced单例门槛（WL≤5%，CPD≤3%） |
|---|---:|---:|---|
| diffeq | +4.4271% | +0.5795% | 通过 |
| frisc | +4.6592% | +0.8758% | 通过 |
| elliptic | +3.9336% | +3.8565% | CPD失败 |
| clma | +3.2157% | +0.6625% | 通过 |
| spmv | +7.7696% | 0% | WL失败 |
| softmax | +8.9117% | +3.3879% | WL和CPD失败 |

六例均native合法，但只有3/6通过Balanced单例门槛；WL几何平均+5.4655%，CPD+1.5495%，不支持Strict 2%或完整Balanced主张。
旧spmv约+57.91% CPD退化仍须保留；后验weight128修正不能抹去该结果。
阈值失败原因已由指标直接确认；不能仅凭指标断言唯一算法根因。PR加性/量化路径delay、共享树seed与native RC/STA目标差异是需隔离的机制。

状态驻留确有实现：XRT BO常驻、四份Resource、连续差分上传和host mirror。search仍在每次kernel调用清零seen/closed/read_epoch，因此不能声称整个搜索工作状态跨调用复用。
路径read-set只覆盖返回路径；`allow_overuse=1`明确跳过version/capacity冲突拒绝，且现有test显式要求stale read在此模式提交。
这支持协商拥塞模式的指定行为，不支持所有模式均严格串行等价。
本次没有找到把用户所指“状态驻留/冲突反例”逐项映射到修复提交、最终硬件版本及终态回归的闭环清单，判定为**修复未证实**，而非断言全部已修复或全部有错。
混合owner/重复net、跨wave replay、差分mirror与路径外成本变化的合法调用边界必须在最终版本补证。

## TilePlace

`tileplace_new_cohort_2026-09-29/summary.json`及`final_audit.json`包含完整13例分母。
本次重新核对两次重复的18份search报告及全部404份trial native JSON、关联小型文件哈希，并核对trial的WL/CPD与原报告一致。
404份记录均为native合法、exit0；这不是404次新运行。实现指纹统一为`2fa6e2324a971d8489bba12d49115f91d0a56874c0ee5200224d72e4f8a9f689`。
9例完成，成功子集CPD几何平均−1.944246%、WL−0.213172%；逐例见`PHASE1_CASES.csv`。
adder baseline缺架构model；ex1010/s298/s38417在30轮CPU路径输入生成后分别剩8/2/2个overuse，未启动refinement；不能记成零收益成功样本。
这些设计已有上游使用历史，不叫strict unseen。

October 4基线：五事务终态5/150、四事务4/120均exit0、完整typed输出一致、cosim PASS；本次核验冻结文件和绑定日志。
九例native审计记录202 trials、88 color calls；独立input audit记录129个唯一输入。本次读原审计及引用绑定，未重跑完整native回归。
该CPU/HLS映射实现指纹`6877e074...`与September Python算法指纹不同，应通过差分证据连结，不能当作同一源哈希。
后续best-dimension-guard物理链最高记录仍为4 ns下WNS −0.047 ns、TNS −3.488 ns、224 setup failures；小型timing/route/DRC报告哈希匹配。
其它候选不能继承October 4功能验收；OOC还排除平台I/O与板卡运行。

旧V4问题必须展示：相同diffeq初始timing报告，generic parser提取52条而历史37条，最终1次接受而历史5次；6.59759 ns/9098不复现6.53077 ns/9105。
restricted诊断只匹配部分历史案例，不能证明历史统一源码。旧六例−5.049% CPD表只作历史数值，不能进入当前固定算法主结果。
已有fixed-source frontier suppression消融：272次native检查、四开发例CPD收益为0，diffeq closure由8增至16，仅WL 9103→9098；否定“此机制解释主要CPD收益”的叙述。
pressure-prefix只有一个开发例的完整refinement进程1.285×历史测量，不能跨到大案例、硬件或完整P&R加速。

## RouteCast

最新handoff、RESEARCH_PLAN与10月21日受控评审一致：原预测目标未验收、strict unseen=0、无完整流程净收益。
`mmc_multiplacement_quality_v1_2026-10-18/cohort_research_decision_v1.json`明确三次已暴露设计swap未通过cohort gate；case01约98.5%改变路径在endpoint-dirty closure之外，直接限制“只修局部端点就能预测全局重布线”假设。
早期固定ABC库有15/177/82个强制拥塞冲突；后续不能仍笼统写成“三例全部容量失败”：受控评审已有两个已暴露案例的容量功能证据，但case02质量失败、case03 LIMIT_REACHED，未形成三例容量+质量+成本验收。
固定库UNSAT不等于完整RR不可路由；预算触限不等于UNSAT。
止损最晚时间为2026-10-24 03:17:53 UTC，已经过去；本次不重开窗口、不扩展同信息局部变体。

NET-local模块的实质是固定其它net占用`O=L-U`，同source连续查询保留Dijkstra labels/frontier。
当前源码按net/connection排序、同source断言、每个net复制ledger；未实现跨placement/history/RC变化的cache失效协议，也没有生产级nonnegative输入准入。
单个largest mux ABBA原搜索均值69.1169s、shared42.1519s（约1.640×搜索阶段）；protocol/receipt绑定本次匹配。
原始setup另记7.1467s；serialization、native routing/acceptance不在该时间内。不能宣称端到端1.640×，亦不能将错误预测的语义等价说成预测质量改进。

## DieRoute

`research_plan.json`指向v292，matrix SHA本次匹配，含448项分层claim但`research_complete=false`；G1–G8没有一个总体关闭。
三开发例联合baseline非退化证据有严格范围；reserved最初15次含10次packing失败，apex2五seed只有3/5联合通过；后验12例全部合法但11/12联合通过，不能替换reserved分母。
adaptive迁移backpressure降低而remote reads/总时间上升，两项质量门槛失败；组件局部证明不等于异步跨die系统或真实SLL收益。
已完成候选在3.333 ns仍WNS −1.236 ns、TNS −12223.346 ns、36299 setup失败；新候选/后续源派生证明不能覆盖物理门槛。

11月7日暂停交接优先于matrix中的旧running观察。本次boot ID与交接一致，但五个记录PID均不存在，完整builder终态JSON仍不存在。
只作“暂停现场已无法由这些PID恢复、退出原因未知、无成功终态”结论；没有信号操作，也不据此启动替代任务。
原field0 `used mismatch`失败与后续短回归都保留；完整四字段、全池、原28878调用、AXI链路是不同门槛。

## FusionPAR

直接链接PR六文件和实际调用TP封存代码已由CMake、runner与retained_router源码确认。
分支保留按不变端点保留完整路径，独立按net重算共享占用；它减少部分路由工作，但当前版本范围仍保守，非最小footprint并发算法。
18次开发运行有6次QoR提交，保留早期I/O格式失败和修复；两个重复不构成稳定性能结论。
15次TP→PR均合法，却0/15通过共同2% QoR门槛；ex5p/alu4/misex3 CPD分别到6.63478/6.80247/5.95697ns，不可拿退化基线算speedup。
九预算TP强参考重跑15次、审计135候选，按共同最终目标挑全部已访问可行候选，包括TP在线拒绝的候选：FP在alu4更好，ex5p/misex3更差；不等于等时间配对。
独立输入4/6可用，s38584.1和tseng的pclk拒绝保留；80次host运行、440候选含35提交/405拒绝。
九评估预算反馈在apex2/seq/spla较盲选更差、des持平且更慢。原生adapter包含序列化/Python/VPR；router为独立区间，不能叠加嵌套timer或把全部remaining host当candidate时间。
这些结果足以保留框架功能，不足以支持“融合普遍优于独立TP/分阶段”的论文主假设。

## 文稿与追溯入口

已核查根AGENTS/GITHUB_UPLOAD/交接、五工程README及上述权威结果。PR有ACM旧稿`paper/dac/main.tex`，TP已有IEEE工作稿`paper/dac2027/main.tex`；DR为研究证据草稿，RC/FP没有paper目录。
完整结果以机器记录和源绑定为先；旧README/paper的“当前”字样不覆盖较新的失败和未采纳状态。
候选结论见`PAPER_SELECTION.md`，门槛见`OPEN_GATES.md`，逐项路径与文件SHA见`CLAIM_EVIDENCE.csv`。
