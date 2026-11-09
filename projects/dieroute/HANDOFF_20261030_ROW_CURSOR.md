# DieRoute 安装行终点复用候选 — 2026-10-30

原目标未完成；权威矩阵仍v169/314条，八门槛、11语料/311096搜索、正式45槽及原预算不变。此文件记录独立私有候选，不替换当前运行源或论文评测快照。

候选 `work/resident_install_row_cursor_candidate_20261030` 从 population shift/add 候选五源文件派生，只修改 protocol.hpp 的 reverse/portal 安装循环：首节点仍执行原起点读取，此后复用上一节点的终点。Rows 已在 prepare 中建好且循环不修改 Rows；两次调用具有相同 kind/index、状态和输出，逆变换逐字恢复父源。接口、容量、公开读取和 watchdog 不变。

ASAN/UBSAN 原始28878调用全部预期回复通过，输出与父候选逐字相同。额外256个有效小图、3072次输入变异/命令边界，共56085次父子回复差分比较通过；不把变异都计为非法输入，判定来自父子完整回复比较。见 host_correctness_review.json 及 host_command_receipts.json。

独立 host_index_profile 在父子两端重放原始完整程序，保留全部预期回复检查。每次成功安装 select 调用11826394→10279852，减少1546542=2*(773272-1)；prefix steps137430244→119884716，word visits53258628→46302062。两次成功安装分别在调用1/session1和28875/session3；两个失败安装调用数仍为0。计数是主机执行行为，不能乘 II 当 RTL 总周期。

原生 Vitis HLS2022.2 csynth 真正退出0，117.291秒，峰值1814269952 bytes、未触发12GiB自身/72GiB全局守卫，原20GiB启动条件保持。独立报告与源绑定复核：LUT114615→114704，FF69248→69506，DSP73、BRAM18K86、URAM42不变，估计时钟2.563ns不变。总延迟仍undef；不能宣称板上频率、fit、RTL加速或十亿周期通过。见 independent_HLS_comparison_20261030.json。execute调度中有cursor load/phi证据，单独见 cursor_schedule_evidence_20261030.json；不是动态RTL调用数证明。

本候选尚未启动任何RTL仿真，不继承父候选的1/28878进度或正负向证明。后续需要相同完整原图、原28878向量、原十亿累计周期、原全部回复/Cpost/observer/性能行和独立正向审计；正向通过后才可运行负向观察器测试。若继续派生原生setup，必须保持父流程源/缓存/155端口绑定和资源守卫，不能把小图差分或综合exit0当作完整验收。

原7条仿真、2终态监控、2后续队列在本轮实际PID/startticks核验均live，CPU增加；主primary当前批次5/256，三个候选仍1/28878。观察文件仍为CSR目录 latest_all_jobs_verified_wait.json。没有重启、停止或修改任何活动任务。本候选HLS已结束，后续不会自动启动RTL。

依赖审计仍需完整传递闭包；新的候选文件不继承此前1753文件库存覆盖。U280仍无实卡，无实卡速度/能耗、平台fit或300MHz达标结论。详细全局恢复入口仍 HANDOFF_20261030_PAPER.md 与原 HANDOFF_20261021.md。
