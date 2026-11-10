# PR0 紧凑交付索引

结论：**INSUFFICIENT_TRACE；本轮结束，停止当前提交协议独立论文假设。**
仅修改独立分支 `audit/pr0-semantics-20261110` 的本目录；主分支、旧结果与其他工程没有改动。仓库公开设置沿用作者已有授权。

| 文件 | 用途 |
|---|---|
| [PR0_DECISION.md](PR0_DECISION.md) | 具体数据、准入逐项判断、结项与不可宣称项 |
| [PR0_PROTOCOL.json](PR0_PROTOCOL.json) | 首轮运行前冻结协议 |
| [PR0_CORRECTNESS_ADDENDUM.json](PR0_CORRECTNESS_ADDENDUM.json) | 同一批快照的当前成本复核补充，运行前冻结 |
| [RUN_IDENTITY.json](RUN_IDENTITY.json)、[source_manifest.json](source_manifest.json) | 协议commit、原始源码及8个实际输入身份；历史source未知保持unknown |
| [SEMANTICS_AND_PRIOR_ART.md](SEMANTICS_AND_PRIOR_ART.md) | 四层语义与直接已有工作（短表） |
| [CAPACITY_VS_POLICY.md](CAPACITY_VS_POLICY.md) | 容量／策略／历史归因与软件计时边界 |
| [replay_cases.csv](replay_cases.csv) | 32快照×4模式=128行；来源、flags、读集、状态SHA、计数、拒绝、结构与重复性 |
| [current_cost_inspection.csv](current_cost_inspection.csv) | 同32快照上的旧路径、S路径、旧/当前成本与变化资源 |
| [timing_samples.csv](timing_samples.csv)、[summary.json](summary.json) | 独立性能模式原始ns与派生ms；无统计加速主张 |
| [counterexamples/README.md](counterexamples/README.md) | 16个小图事件/边界及1个不同sink共享trunk的精确范围 |
| [historical_attribution.json](historical_attribution.json) | 原clma两臂小型日志来源、终态及未知失败类别；不是新历史复现 |
| [local_artifact_index.csv](local_artifact_index.csv) | 只索引本轮新runtime文件；原路径、大小、SHA；二进制不上传 |
| [evidence/](evidence/) | 原始小型CSV、外层墙钟ledger、RSS、可执行文件SHA、终态 |
| [code/](code/) | CPU隔离诊断、机械参考生成器、资源限制执行器与结果汇总脚本 |

本地runtime：`/inspire/hdd/project/siinovarch-fpga-chip/guoruiyuan-253208540291/FPGA_Acc_PR0_RUNS_20261110/`。
初始图/任务输入保留在原仓库 `projects/persistroute/experiments/balanced_pathreads_matrix_2026-08-28/{diffeq,clma}_seed1_cw200/input/vpr_input.*`，本轮只重哈希这8个小型二进制（合计约21 MiB），未重扫旧 work 或759 GiB数据。新冻结资源快照、任务、seed、可执行文件均留本地，不能只克隆GitHub就假定这些大输入存在。`local_artifact_index.csv` 的快照SHA可供服务器独立核验。

解释CSV时：

- q编号是每设计0…15；iteration=0、wave=1、batch=0/1，取样发生在生产控制器排序与cost初始化之后。所有seed仅根，故不覆盖真实后期多seed/ripup；小图补充不能代替该分布。
- `search_status=1`为候选成功，`commit_status=4`为提交、2为拒绝、3为搜索/容量等失败；没有把3统一写不可达。
- 原始 `cost_diff_S` 比较两次搜索各自快照的返回值；判断旧路径当前代价用补充的 `old_path_current_cost_diff`。这两个字段不能互换。
- `read_unique` F为评分与路径依赖并集，P/N/S为路径记录；`score_unique`与`resource_load_calls`来自批次快照的宽观察器，所有模式共享该观测列，**不是**每个S重执行的独立读集测量。
- `queue_peak`同样是批次快照观察器的峰值。`structural_ok`检查候选图结构及seed归属，并不证明全网树/所有权集合/native合法性；`state_consistent`表示相应有限四副本/候选对照通过。
- F的task/seed/graph在同快照回放中固定，并用SHA绑定；这里没有跨回调变化的自动F缓存。参数变化的合同由独立小图说明，不应称完整可部署依赖机制。
- `logical_record_bytes` F为id4+Resource16，P/N为ReadEntry8；只是规范化存储载荷，不含allocator、bitmap、vector capacity等，也非DMA实测。实际程序峰值RSS另记。
- 正确性CSV计时包含观察，不作性能比较；`timing_samples.csv`才是单独性能调用。每查询顺序S/F/P/N、各一次，存在缓存/顺序偏差，无置信区间或speedup声明。

复核首轮实现时应检出 `b5518828a14c61211bcd0f49600166b04ea48bcc`；`source_manifest.json` 的诊断源哈希是该预运行版本，不能与之后含 `inspect` 函数的文件混认。补充实现检出 `a700afbe3ff22038529e450901ba9bd06f5fcc2d`，绑定于 `PR0_CORRECTNESS_ADDENDUM.json` 和 `evidence/supplement_identity.json`。两次实际编译/执行 argv、终态和累计墙钟在 `evidence/run_ledger.json`，运行不能覆盖本地现有目录；复核需另选新目录；新的计算不在本轮结项范围。本轮不再启动任何复核实验。

硬件/FPGA相关源码解释曾使用 [hls-pragma-scope 技能](/inspire/hdd/global_user/guoruiyuan-253208540291/codex/home/plugins/cache/amd-ross-agentic-ai-assistant/amd-ross-agentic-ai-assistant/2026.9.1/skills/hls-pragma-scope/SKILL.md)，只帮助阅读pragma范围；没有打开Vivado会话或运行FPGA流程。
