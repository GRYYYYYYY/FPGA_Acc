# PR0：四层语义与直接已有工作

范围：b32afa4303a5574dde7171b4ae6e3d07aeb8a06c 的 CPU 搜索/提交及其控制器。
本表区分代码合同、有限观察与尚未证明的性质；不把名字相同的 MultiQueue 当成相同算法。

| 层次 | 现有实现的合同和边界 | PR0 观察；不能扩大的结论 |
|---|---|---|
| 结构与状态正确 | search 输出 RR 路径；controller `accept_path` 检查 attachment、边、树重入；Owners 按 net 集合重算占用。commit 先校验后写四副本；它本身不检查边或父树。XRT host 有 `mirror_commits` / `sync_resources`。 | 32 查询窄/宽参考匹配、图结构检查通过；固定提交顺序重放与实际 C-model batch 状态相同；独立四数组提交及失败回滚通过。不同 sink 共 trunk 的小图占用为1。**没有**动态运行 XRT mirror/差分上传；混合 owner、多轮重复 net 和全树一致性不因此全覆盖。 |
| 最终可行 | `route_success` 要求所有任务完成且无 overuse，`validate_pathfinder_result` 再检查；native VPR 是另一个必要层次。常规 negotiated wave 允许中间 overuse。 | PR0 在第一轮第一 wave 的前两批截断；final legality/WL/CPD 均 unknown。历史 corrected 六例 native 合法、仅3/6过 balanced 门槛，仍是原审计范围。不能用本片段代替闭环。 |
| 重复确定性 | 当前 CPU heap 的全8 bank 最小值选择、成本/hops/predecessor tie、priority/id 提交顺序是确定的代码路径。不是随机 two-choice relaxed MultiQueue。 | 同一快照重复的32查询一致；不等于所有配置/线程数/最终硬件已证明确定。跨状态路径不同不是重复确定性错误。 |
| 当前状态串行等价 | 常规 wave 没有这一承诺。路径读集既不覆盖所有成本输入，`allow_overuse=1` 又跳过 version/capacity 拒绝。即使 P=0，通过也只约束指定路径资源，不能证明最优选择仍新鲜。 | N 有10/32路径及当前成本不同于同算法固定顺序重执行 S。F 保守校验失败后重放，在此样本匹配 S；这是有限差分，**不是完整动态依赖的通用证明**。串行等价不是所有并行 PathFinder 的必需合同。 |

调用链：`accelerated_pathfinder.cpp:240` 的常规 wave 明确传 `true`；cleanup 的两处 executor 传 `false`（本轮 passes=0，没有执行）。C-model 将 flag 传至 commit，XRT host 也按 bool 转0/1传入。`Task.epoch` 在控制器表示轮次，backend 调用 search 时重写为 seed 数量，`reserved` 是 seed 数组偏移；不能只拿原 epoch 当失效证书。

P 在本实验特指同候选的 `allow_overuse=0` 路径版本/容量检查；N 才是常规真实 flag。F 比较实际评分读取及路径依赖的 **完整 Resource 字段**，同时固定 graph/task/seed；发生变化后运行 S，再按 negotiated 合同提交。F 不要求每步容量零超用。S 是当前状态的生产搜索，不是 VPR 或独立最短路正确性证明。

| 原论文／官方实现 | 与 PR0 最直接的重叠与区别 |
|---|---|
| [AIR，ASP-DAC 2020](https://ieeexplore.ieee.org/document/9045175)；[官方 VTR v8.0.0 route_timing.cpp](https://github.com/verilog-to-routing/vtr-verilog-to-routing/blob/v8.0.0/vpr/src/route/route_timing.cpp) | 已读官方 `setup_routing_resources`：裁剪路由树、保留合法分支、同步占用/traceback并只重路由剩余目标。因此“避免重做”和“局部树复用”本身不是新方法。AIR 原论文正文未成功获取，不据此作其所有优化/语义的完整查重。 |
| [MultiQueue-Based FPGA Routing，作者原文](https://www.alex-singer.com/assets/publications/conference-papers/2024-FPT-parallel-fpga-router.pdf)，§II–V | 单连接搜索的细粒度并行；对 Dijkstra/A* 用 stopping/tie 等规则保证确定性及串行等价，directed search 合同不同。本文承认并分析 AIR；PR 是多查询快照与提交问题，当前8-bank严格选择也不同于其 relaxed queue。不能把该论文的正确性保证移植到 PR。 |
| [CUFR 原文](https://arxiv.org/html/2407.00009v1)，§3 | 三叉递归划分安排并行连接，present/history 混合更新消解拥塞。共享资源、调度、协商以及最终无 overflow 已有直接先例；不代表当前路径读集具有严格串行等价。 |
| [Potter 官方仓库与 README](https://github.com/diriLin/Potter/blob/main/README.md)，含期刊/会议原文链接 | overlapping bounding boxes 并行路由已有实现；Potter-S 声明确定性，Potter-R 追求运行时间且不确定。README 的确定性不能自动升级成同固定串行顺序等价。本轮未构建或测试 Potter。 |

以上核查未找到“相同 PR 输入、ABI、flags、成本与控制顺序”的已发表实验可直接替代本轮；这只说明不能跳过定向诊断，**不证明新颖性**。缩小读集、版本检查、允许协商超用、状态常驻均不能单独作为新贡献。

最终 tree-seed 硬件清单 `u280_treeseed_hw_2026-08-29.json` 仍为 `hw_emu_rerun=false`；早期硬件仿真不能覆盖它。CPU四数组一致和逻辑字节均不是最终RTL、HBM带宽或实体U280证据。
