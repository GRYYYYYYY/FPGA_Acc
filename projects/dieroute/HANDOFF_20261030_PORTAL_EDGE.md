# DieRoute 恢复入口：portal安装边编号内部读取候选 — 2026-10-30

原目标未完成。当前矩阵仍v169/314条、关键路径 experiments/critical_path_20261030_v169.md，八门槛均开放，11语料/311096搜索和45正式槽保持；正式终态37通过/8存储失败不替换。原要求仍 HANDOFF_20261021.md；原8条仿真/监控和完整原始RTL验证背景见 HANDOFF_20261030_ROW_CURSOR_RTL.md，论文/文献/依赖审计背景见 HANDOFF_20261030_PAPER.md。此处为新增私有候选，不更新研究覆盖或替换活动源。

新增 `work/resident_portal_install_edge_candidate_20261030` 从row-cursor五源文件派生。只新增Store内部安装用 portal_install_edge 方法，并替换portal目标节点检查处的get(7)调用。只需边编号却重建源节点的二分查询被移除；i<p、pool边读取、edge<e、pool根读取及cost字段读取检查仍保留。公开get方法和协议公开read分支源后缀逐字相同；逆变换逐字恢复父五源。方法只用于prepare和所有portal put(7)成功后的安装阶段，不提供新的外部协议。

等价前提见 derivation.json：prepare成功建立不可变、非降、起始0/终止e的forward offsets及每节点分隔符。对edge<e，source的upper_bound不会返回0，每次offset(mid)都存在；edge>=e由原source和新范围检查同样拒绝。安装期间没有Rows写入，故安装站点可以用范围检查代替不被使用的source重建。此证明的适用范围是Protocol安装，不泛化为对未prepare Store任意状态调用新方法的等价。

ASAN/UBSAN原始28878全部预期回复通过，与父输出逐字相同；256有效图/3072次输入变异，共56085父子回复比较通过。source范围有限oracle v2枚举n1..6/e0..8的全部5004个不同弱组合，32031偏移/43614边界检查通过，唯一性与binomial理论计数一致。原首版oracle从index1开始导致首行固定为空和重复fixture；其exit0不证明穷尽覆盖，旧源码/日志完整保留，oracle_coverage_correction.json说明v2修正。接受的范围oracle仅为v2；有限测试支持而不替代上述等价证明。见 host_correctness_review.json。

host_index_profile分别对父子源码插入相同计数器、逆变换恢复原源码，并重新执行全原始程序/全部预期回复。两次成功安装call1/session1与28875/session3：source_calls170628→0，select_calls10279852→6927996（减少3351856，约32.6%），prefix_steps119884716→80345551，word_visits46302062→31162137。两个失败安装的计数仍0。计数只说明主机执行，不能乘II当RTL总周期；公开查询中的source保留。

原生Vitis HLS2022.2 csynth真正exit0，114.305秒，峰值2026487808bytes，原12GiB自身/72GiB全局/20GiB启动守卫无触发。独立报告/源与主机证据绑定复核通过：LUT114704→119914（+5210），FF69506→72391（+2885），DSP73→87（+14），BRAM18K86/URAM42不变，估计时钟2.563ns不变、总延迟undef。生成DUT文件95→96，仅增加portal_install_edge.v。不能把这些估计当routed fit、实卡频率、RTL加速或watchdog验收。见 independent_HLS_comparison_20261030.json。

installation_callsite_review_20261030.json独立核对父子execute调度：安装get(kind7)启动/完成两阶段替换为新helper的两阶段，公开动态kind get的两阶段仍保留；新helper直接调用不含source/select。两阶段不是两次动态调用。该静态证据支持调用点变更，不是整体RTL等价或周期测量。

本候选尚未做原生cosim配置或启动RTL，不继承row-cursor的1/28878进度/监控绑定/正负向证明。后续若启动完整验证，需按ROW_CURSOR_RTL流程从本次96DUT新综合产物生成监控，prj必须包含新增helper，重新构建只含此两处代码差异的Cpost，核验155端口/原完整TV缓存/全部源与资源守卫；固定原图、28878调用、十亿累计周期和全部审计。正向独立通过后才可执行观察器负向测试，不自动重试/采用。

原8条仿真、3终态监控和2后续队列实际身份均live/CPU增加，四候选资源心跳正常，暂无新增RTL验收。poll命令为 python3 -B work/resident_install_row_cursor_candidate_20261030/poll_existing_jobs.py；共享可变记录为CSR目录 latest_all_jobs_verified_wait.json。不能因日志静默或观察超时停止/重启。物理/平台队列仍依原审计和内存前置条件，不因本候选HLS成功绕过。

原完整依赖闭包/创新性对比/全QoR/硬件实现门槛仍需完成。新候选不继承先前1753文件库存覆盖。U280无实卡，无板上速度/能耗、平台fit或300MHz通过结论。所有失败、预算及分母保留，无commit/push。当前文献稿仍独立32页文献更新/22October评测快照，不是最终全实验稿。
