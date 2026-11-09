# DieRoute 恢复入口：位计数候选完整RTL已启动 — 2026-10-30

原目标未完成，历史要求见 `HANDOFF_20261021.md`。当前矩阵v167/312条记录，关键路径 `experiments/critical_path_20261030_v167.md`。以 `experiments/research_plan.json` 当前指针和实际进程状态为准。原11语料/311096搜索、45正式槽、预算和八门槛保持，全部门槛开放。

新候选根目录 `work/resident_population_shiftadd_candidate_20261030`。既有主机全28878和综合证据见 `HANDOFF_20261030.md`，其文件保持冻结。现已完成native小bootstrap配置（30.0755秒/exit0，无正式RTL验收）、匹配Cpost编译、155端口及宽度一致性、95DUT文件一致性、249最终源绑定和8原缓存身份核验。

新完整RTL位于 `RTL_positive_native`，supervisor1598362/start1763639016，pipeline1598513/start1763639029，xsimk1631159/start1763643023。实际三AXI模型time0完成初始化，三个known-write观察器均绑定，当前1/28878只是安装前读取。完整图安装尚无成功证据，不得称RTL通过或采用。原1e9累计watchdog、完整容量、12GiB own/72GiB global/20GiB启动余量保持。

新专用终态监控1705028/start1763652383，仅观察新候选；原监控2315028/start1756238319继续观察dictionary和CSR两条旧候选。两个根目录均有 `terminal_watcher_protocol.json`、`terminal_watcher_launch.json`、`terminal_watcher_state.json`。各监控等捕获的supervisor/pipeline/xsim全部真实退出，成功后执行 `review_full_positive_v2.py`；失败保留，不重跑。新auditor逐字等于CSR父审计器。原观察器负向X canary已准备，但必须等完整正向独立审计通过后再运行并独立核验。

现有旧句柄继续：dictionary679931/start1756114851、CSR1852355/start1756203622、metadata2851880/start1703080565、joint4039363/start1700583670、Owner710564/start1697480670、primary3488383/start1695089791；物理队列2135063/start1704361242，平台队列2605659/start1700432104。共享可更新观察记录仍为CSR根目录 `latest_all_jobs_verified_wait.json`，已包含11句柄（7仿真、2监控、2队列）。核对两个监控的状态，不要只读旧监控。新候选 `all_jobs_after_RTL_launch_20261030.json` 为本轮静态快照，不能替代实际核验。

完整输入缓存以目录符号链接复用，禁止哈希/复制/稠密化巨量安装TV。新候选 `preparation.json` 的路径替换字段记录的是中间阶段；其中monitor/project两项随后被最终生成文件覆盖。`preparation_metadata_clarification_20261030.json` 已说明；最终protocol、DUT及monitor哈希已核验。未改任何活动绑定源文件。

原正式结果37通过/8存储失败，分母不替换，仅s298seed3满足5/5。物理U280仍不可用。新候选局部HLS改进伴随LUT增加，完整RTL速度、平台fit、300MHz、实卡速度/能耗、论文最终交付均未完成。不要以配置引导、主机重放、部分事务或仿真时间前进代替完整验收。
