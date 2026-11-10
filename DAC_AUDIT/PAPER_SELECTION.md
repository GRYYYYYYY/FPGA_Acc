# DAC 2027 第一阶段选题判断

**只保留A为本届主候选、E为备选；目前没有一个候选达到建议提交完整论文的证据门槛。**
这是依据已有证据完整度、可隔离的方法贡献和剩余补证成本所作的条件选择，不是投稿通过声明，也不按工程规模排名。

官方[Research Manuscript Submissions](https://dac.com/2027/program/research-manuscript-submissions)于2026-11-10核对：摘要11月11日17:00 US Pacific，全文11月18日17:00；对应北京时间11月12日/19日09:00，与任务一致。IEEE正文最多6页，另1页仅参考文献；当前工作稿仍需按这个边界收敛。

## A — TilePlace：主候选，收缩为CPU/VPR方法

核心假设：原生布线反馈驱动确定性事务搜索，在严格合法性与QoR验收下，以精确影响集合和状态复用减少候选/反馈重复成本。
已实现：约束/macro-aware多类事务、稳定冲突选择、native acceptance/rollback、反馈刷新、可重放源指纹，及局部精确prefix优化。
“精确影响集合带来完整流程收益”尚需新机制消融；不要把普通rollback或调用VPR本身叫新方法。
已核查的最强native证据为固定源13案例中9例完成、404份trial记录；成功子集CPD−1.944%、WL−0.213%，4个失败保留。October 4硬件功能差分属于另一证据层。

公平基线应为同packed netlist/architecture、同可执行VPR、同目标、同总wall预算的VPR SA continuation/restart，以及同TP控制器关闭新增复用；已有同netlist SA/AP可以运行，但旧AP timing权重未完整实现，不能独自代表最强现代timing placer。DREAMPlaceFPGA/AMF改变输入和packing的问题已记录，不能直接拼表。
负结果没有否定所有native反馈优化，但已否定“旧frontier suppression解释CPD收益”和“旧V4统一源−5.049%可直接作为主表”。
最少补证：封存一个generic-parser CPU版本；汇出13例全分母及完整计时；独立冻结尚未暴露的新设计；等wall/等closure两个分开的对照；只对一个有明确计时依据的复用机制做on/off；必要的重复与所有失败留存。协议必须在运行前写入分支并记录SHA，当前建议不是已冻结协议。
无U280可成立的最强论文：范围明确的、经native检查的CPU placement-refinement算法及受控完整refinement成本结果；不写FPGA应用加速、板卡频率或能效。硬件作为可选实现可行性附属材料，不追赶4ns来代替主贡献。

## B — PersistRoute：本届不优先

核心候选是持久Resource、固定顺序事务提交和多CU搜索的组合。C-model/XRT数据面已实现，最终180MHz实现存在；最终版本RTL功能连接和同源同参数QoR仍不完整。
公平baseline是完整成本的VPR 16-worker和1-worker，不是C-model或hw_emu速度；已有baseline入口可运行，但板卡对照当前不可运行。
六例WL均值超门槛、半数Balanced单例失败，否定现有配置的质量保持假设；spmv后验权重更换不修复整个冻结协议。
最少补证需最终源功能反例回归、统一QoR政策和版本、驻留/事务消融；若主张实际加速还必须实体板卡。九天内以无卡体系结构分析替代原加速主张，将需要重新建立论文贡献，成本高于A。
无卡最多报告实现可行性、有限功能验证、明确假设下周期/流量分析；目前不能报告真实加速或能效。

## C — TilePlace + FusionPAR：不选

候选贡献是移动影响范围、保留不变树分支和跨阶段事务控制。已有真实PR链接、retained router、原生验证和TP→PR runner；高级TP/RC联动、最小并发footprint与硬件ABI仍是未来工作。
最强可运行baseline已经包含九预算TP全部可行访问点，以及共享状态分阶段模式、空树PR与关闭反馈消融。
现有三设计仅一例胜TP、四独立设计反馈0例更优，TP→PR又15/15质量失败。这些结果否定现有配置的普遍融合收益，不否定所有未来局部复用算法。
最少实验必须在相同最终QoR、相同总时间/预算下同时赢TP、分阶段和无新机制版本，并验证完整准备/adapter成本；不允许只报router局部时间。
无卡可发表的上限是CPU局部refinement方法，但当前差分贡献及收益不足，不能靠组合项目名形成贡献。

## D — PersistRoute + DieRoute：本届排除

候选方法是分区所有权、SLL/corridor协调和分层提交。源码有PR控制层依赖与许多组件证明；真正多die完整系统、所有权并发语义及HBM/原生全链路尚未统一验收。
v292全部八个总体门槛开放，reserved与posterior结果混合，adaptive消融负面，真实物理跨die/SLL与板卡速度均未证明。
强baseline应为原生VPR multidie/可比partial-routing方案及关闭协调机制，不能用不匹配的单die问题作胜出基线。
即使无卡，可信多die软件方法仍需真实架构元数据、统一源完整native cohort和跨die机制消融；当前不足。
本次依用户要求永久限定为审计范围，**不启动或恢复DieRoute实验**。不能为了本届投稿串接未闭合的PR和DR结论。

## E — RouteCast NET-local搜索复用：备选

候选贡献限定为“固定其它NET占用、同源多查询”的等价搜索状态复用，禁止继续包装成已成功拥塞预测。
实现是Python固定上下文Dijkstra frontier/labels复用；已有物理mux和合成比较，以及一个ABBA块的69.117→42.152秒搜索观察。没有完整部署成本或跨族泛化结果。
普通多目标最短路树复用不是新颖性本身；需要证明特定路由owner语义下的固定性、tie/zero-edge/terminal规则、有限查询状态与失效边界，并显示可付清的系统成本收益。
最强公平基线包括优化的逐connection搜索、同样预计算/同ledger策略的NET多目标实现，以及实际消费者native-only；本地前两类基础代码存在，公平完整成本对照尚未验收。
原预测失败不直接否定等价算子优化，但证明其不能以“提升预测质量”解释价值。
最少补证：生产级前提校验和反例；跨族完整hard/soft上下文；setup/serialization/update/consumer全计时；重复ABBA与等复用baseline。固定mux上继续微优化不足以投稿。
无卡可以成立的最强结论是有明确前提的CPU exact reuse算法及消费者净收益；当前只有搜索阶段收益，不满足此结论。

## 与已有工作的边界

- [AIR原论文](https://www.eecg.utoronto.ca/~kmurray/air/aspdac2020_air.pdf)已研究自适应增量路由、减少重复搜索和已有路由改善。搜索可获取原论文文本，但本次直接打开PDF失败；未宣称完成全文逐节复核。
- [VTR v9路由参数](https://docs.verilogtorouting.org/en/v9.0.0/vpr/command_line_usage/)明确存在高fanout合法树复用；[RouteTree API](https://docs.verilogtorouting.org/en/latest/api/vpr/route_tree/)提供剪除非法分支和增量更新。这直接限制C/E把一般tree reuse当首创。
- [DREAMPlaceFPGA-MP原论文](https://arxiv.org/abs/2311.08582)已经覆盖cascade shapes/region constraints；macro与约束支持不是A的独立创新点。

以上是已查到的直接重叠和比较轴，不是完整新颖性证明。A必须以固定信息与完整成本下的明确机制收益立论，E必须以owner语义下的等价性和全成本收益立论；若做不到，两者都不应提交。

## 决策与有限后续顺序

现在的投稿判定为 **NO-GO（证据尚不足）**，同时将有限补证资源集中到A、保留E。
先做第二阶段紧凑证据整理和来源闭环，不启动大规模VPR/HLS/Vivado计算。只有在确认现成baseline可公平运行、一个机制有成本依据、案例未见性可证明后，才冻结A的最小实验协议。
建议11月11日北京时间晚前完成摘要决策：摘要只能写已完成结果；不能预告尚无证据的速度或未见设计胜出。
建议11月16日北京时间晚作为完整实验止损点，保留两天写作/复核；到时若新贡献、来源、全成本公平baseline或失败分母任一关键项未过，维持不投稿，不转去临时拼接B/C/D。
此时间点为本次建议的内部门槛，尚未触发任何实验。

IEEE 6+1页修改计划（基于现有`projects/tileplace/paper/dac2027/main.tex`）：
1. 约0.75页：问题、现有工具不足和单一可检验贡献；摘要限定已通过的结果。
2. 约1.5页：事务/反馈闭环与实际新增复用机制，适用条件、失效规则、正确性论证。
3. 约1页：固定源码/输入、失败分母、两类预算、强baseline、计时边界和新设计准入。
4. 约1.5页：全案例QoR、完整成本、单一机制消融；历史V4问题与负结果不能消失。
5. 约0.75页：已有工作、局限、复现与结论；硬件最多一个独立小表，未过4ns照实标注。
6. 约0.5页留给版面调整及最终作者信息空间；参考文献独立第7页，不放其它内容。

本文件是第一阶段选题判断与修改计划，不冒充最终交付 `FINAL_DECISION.md` 或已验收论文。
