# 当前论文假设结项 — 阶段 2B 后

日期：2026-11-10。最终状态：**KEEP_ENGINEERING_OPTIMIZATION_ONLY；当前论文假设已结项**。本轮仅追加结项文档，不是阶段 2C，不启动新实验。

证据基准：`0f93dc122d704379007130dde2fa394344e587a2`；阶段 2A 基准：`2019e8fc5bb410cb2a4b1d9bb5f557dc5682b08e`；原源码基准：`b32afa4303a5574dde7171b4ae6e3d07aeb8a06c`。下列已有文件均引用该冻结证据树，不重建或复制实验包。

## 分开结项的两项判断

**工程状态：R1 有效，保留隔离可选实现。** R0/R1 均开启已有 prefix；仅切完整参数及压力快照版本的普通精确缓存。两例全候选事件摘要、原生闭环及补充合成测试在声明范围内一致。R1 未移植至生产入口、未合入 main；未来移植必须针对新入口、状态生命周期和正确性另行回归，不能继承本次验证范围。

**论文状态：关闭当前评分复用独立贡献路线。** 未建立超出普通缓存的独立方法贡献，也未定位公平 R1 不能实现的额外必要能力，R2 不实现。当前证据不支持进入正式论文矩阵，不能继续用当前冻结 TP 主张强原生基线优势。这不否定所有布局精化研究，也不删除 TilePlace 工程。

## 已接受收益与原生反例

| 已暴露开发案例 | R0 完整 refinement 中位数 / s | R1 / s | 时间减少率 | 允许墙钟预算 / s | 冻结 TP：CPD ns / WL | 原生最终：CPD ns / WL |
|---|---:|---:|---:|---:|---|---|
| diffeq | 72.830 | 49.247 | 32.38% | 90 | 6.59759 / 9098 | 6.59759 / 8900 |
| clma | 382.353 | 316.888 | 17.12% | 450 | 11.5929 / 79926 | 11.4244 / 78815 |

每臂每例只有两次性能样本；原始值见 [runtime_samples.csv](phase2_B/runtime_samples.csv)。这些是相对 prefix-on R0 的执行收益，不是相对 VPR 的加速比，也不与阶段 2A 不同批次的倍率相乘。

两例原生最终结果均支配当前冻结 TP：diffeq 同 CPD、WL 更低；clma CPD/WL 均更低。原生采用从共同合法 B0 出发、固定种子序列的 fresh-SA incumbent 循环，不是 SA 检查点续跑；共同接受规则和截止前必要验证不变。两个窗口分别完成 49/45 个合法候选、接受 7/6 次更新，各保留 1 次截止中断，未使用中断候选的后验结果。合法 B0、全部拒绝与截止状态保留，见 [等预算结果](phase2_B/equal_budget_pilot.csv)及下表原生记录。

此结论只针对**已测两例、固定控制器及 90/450 秒预算**。TP 按旧 epoch/closure 上限提前结束，原生仍可继续搜索；比较的是同一允许墙钟上限下的固定策略，不是相同 CPU 秒消耗，不证明任意扩展预算后的 TP 都失败。TP 质量—时间曲线复用本轮性能运行，事件时间保留其保守上界；这不是新的 TP/native 配对计时。经验摘要差分不构成任意输入形式化证明。RSS 仅为 Python 进程自身峰值，不是进程树峰值或缓存独占内存。新 **cold-deployment = unknown**，不拼接历史准备时间。完整解释见 [阶段 2B 总结](phase2_B/PHASE2B_SUMMARY.md)和[成本诊断](phase2_B/COST_DIAGNOSTICS.md)。

## 保留的可复用资产（实际路径）

| 资产 | 已有文件与来源 |
|---|---|
| prefix 与冻结参考算法 | [phase2_A/source/tileplace_v2.py](phase2_A/source/tileplace_v2.py)；保留阶段 2A 冻结实现 |
| R1、切换入口及容量 | [phase2_B/reuse.py](phase2_B/reuse.py)、[entry.py](phase2_B/entry.py)、[PROTOCOL.json](phase2_B/PROTOCOL.json)：完整语义键、131072 条 FIFO、仅压力替换失效；R0/R1 均 prefix-on |
| 完整实现身份及真实执行组合 | [phase2_B/source_manifest.json](phase2_B/source_manifest.json)、[PRE_RUN_COMMITS.json](phase2_B/PRE_RUN_COMMITS.json)、[binding_validation.json](phase2_B/evidence/binding_validation.json)：阶段 2A 冻结源，加 entry/reuse、[supervise.py](phase2_B/supervise.py)及实际调用的 [phase2_A/source/run_tileplace_v2.py](phase2_A/source/run_tileplace_v2.py)，共同构成有效实现；不能只沿用旧七文件指纹。工具与输入身份另见 [phase2_A/source_manifest.json](phase2_A/source_manifest.json)及各运行 provenance |
| 全枚举观察器与 chunk 摘要 | [entry.py](phase2_B/entry.py)、[observer_event_map.json](phase2_B/observer_event_map.json)、[correctness_summary.json](phase2_B/correctness_summary.json)；详细摘要位于 phase2_B/evidence/ 下各 correctness 运行目录 |
| stale-key 与 macro/chain 反例 | [unit.py](phase2_B/unit.py)、[fixture.py](phase2_B/fixture.py)、[FIXTURE_PROTOCOL.json](phase2_B/FIXTURE_PROTOCOL.json)、[fixture/stdout.json](phase2_B/evidence/fixture/stdout.json)：有限参考向量、数值负控制和合成枚举结果，不替代真实原生合法性检查 |
| 原生预算执行器及共同接受规则 | [phase2_B/baseline.py](phase2_B/baseline.py) 与 [phase2_A/source/run_tileplace_v2.py](phase2_A/source/run_tileplace_v2.py) 的 acceptance_reason；执行命令、种子与 incumbent 链保留在原生记录 |
| 质量—时间点、拒绝与 cutoff | [quality_points.csv](phase2_B/quality_points.csv)、[equal_budget_pilot.csv](phase2_B/equal_budget_pilot.csv)、[diffeq_native/baseline.json](phase2_B/evidence/diffeq_native/baseline.json)、[clma_native/baseline.json](phase2_B/evidence/clma_native/baseline.json) |
| 证据索引与复算工具 | [evidence_index.csv](phase2_B/evidence_index.csv)、[verify.py](phase2_B/verify.py)；既有复算与 SHA 核验已通过，本轮不重复运行实验或重建归档 |

主实验运行前提交为 `eb0a9c5e16e6c15b89cc2f91362519aab55b792a`；补充成本诊断协议为 `11866c25fc69dddf473f0f6aadf7539dfcd0aa49`；实际执行的合成测试修订为 `c19468aaa696a85c23662b566f290e3307bedb13`。最终证据统一固定于本记录开头的阶段 2B 提交。

## 停止边界

不执行 R2、缓存变体/容量/阈值搜索、追加 VPR 矩阵或种子、扩大 TP 预算、补硬件，亦不为当前主张补 cold 实验。不自动激活 E，不自动恢复 B/C/D；DieRoute 保持不运行。main、仓库可见性、原始现场和阶段 2A/2B 证据不变；不修改其他仓库，不重扫 759 GiB，不代作者注册或投稿。

未来只有在作者另行提出实质方法问题、说明其与普通缓存及原生搜索的区别，并解释为何不会重复当前负结果时，才有重新讨论的前提。此条件不是下一轮执行授权。本轮在正常追加提交后结束，后续科研资源选择由作者决定。
