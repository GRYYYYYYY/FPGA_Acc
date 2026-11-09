# DieRoute 恢复入口：扩展作者论文方法对比 — 2026-10-30

原目标未完成。历史目标见 `HANDOFF_20261021.md`；当前矩阵v168/313条记录、关键路径 `experiments/critical_path_20261030_v168.md`，以 `experiments/research_plan.json` 当前指针为准。原11语料/311096搜索、45正式槽、预算及八门槛保持，所有门槛仍开放。

新增G8证据位于 `work/rwroute_thesis_extended_methods_review_20261030`。扩展阅读Yun Zhou2022作者学位论文3.4.3、3.5.1、3.7.1-3.7.2（PDF115-120/130-132页），逐项绑定提取文本行号、页码和源SHA。官方新下载PDF与原缓存SHA一致。不是2022期刊论文正文审阅，也不是206页完整审阅。

六项观察涉及：保留既有合法布线、时序/criticality与同网共享、只重路由冲突网并屏蔽保留资源、四边逐步扩框、局部STA所需FF边界时序隔离、部分路由例中CPD相同的具体范围条件。DieRoute须明确区分authority/publication/reservation，计入完整安装和STA生命周期成本，并继续验证全设计QoR；未据此证明创新性或可比加速。

`catalogue_snapshot.json` 完整保留原9来源条目，再加入作者学位论文和固定版本官方代码两种来源，共11来源记录，不是11篇论文或11项复现。plan中的G8范围描述已校正；根论文、旧目录及旧证据保持冻结。锚点首次因PDF的ex-/pands断行匹配失败，修正为唯一连续词组，记录在 `citation_anchor_correction.json`，没有改原文。

下一项可独立推进的工作：从已有证据稿创建仅更新相关工作的私有fork，补入作者学位论文引文和有界方法对比，保留原评测快照日期与范围，编译并检查相关工作页面。不把新增文献当硬件/性能/最终验收结果。

并行RTL及句柄详见不变的 `HANDOFF_20261030_RTL.md`。7仿真、2终态监控、2队列仍以实际/proc身份和终态回执核验。共享可更新观察文件仍为CSR候选的 `latest_all_jobs_verified_wait.json`，其中还记录三个候选的supervisor/pipeline身份和资源守卫心跳。不得因静默重启或增大watchdog。

三个完整28878候选的正向审计通过后，负向观察器执行入口为 `work/full28878_observer_canary_tools_20261030/prepare_and_run.py`；默认只读检查，加 `--run` 才会在所有前置条件通过后创建单次负向实验。P1用 `--positive-case RTL_positive_native_monitors_v5`，P2/P3用 `RTL_positive_native`。当前三者都没有完整正向证明，预检均返回75，未创建负向实验。

原正式结果37通过/8存储失败保留，只有s298seed3达到5/5。原输入缓存不重哈希/复制/稠密化。U280仍不可用，无实卡速度/能耗、平台fit或300MHz达标结论。原目标、门槛和最终交付范围不缩减。
