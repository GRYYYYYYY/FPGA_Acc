# DieRoute 工作交接 — 2026-11-06

研究目标当前为 **paused**。不自动启动、重试或恢复任何实验。原目标和八个门槛保持不变；`experiments/research_plan.json` 的当前 matrix/critical-path 指针仍是正式基线，旧的运行中登记只是历史启动记录，应以此交接和 terminal 为准。

## 当前实验真实终态

`work/dictionary_builder_full_input_20261106` 的完整四字段 RTL 构建器 XSim **已结束且失败**，不再有该监督或仿真进程。`run_builder.terminal.json` 记录退出码 0、守卫未触发、峰值 RSS 826,478,592 字节、运行约 1,914 秒，但 `run_builder.stdout` 在仿真时间 1,526,818,610 ns 报 `Fatal: field 0 used mismatch 0`；XSim 对此 `$fatal` 仍返回 0。独立终态审核 `work/dictionary_builder_terminal_auditor_20261106/terminal_review.json` 判定 `failed_fatal_or_error_log`。没有 FIELD 0 PASS 或后续字段结果；首字段描述符检查位于出错检查之前且未报错，但不能因此声称字段内容或整个构建通过。

最后原始进度日志为 150,000,000 周期、字段0请求1,521,244次；这是部分活动，不是可恢复检查点或结果。保持失败日志、脚本、波形和初始输入，切勿覆盖或把旧 PID 当活任务。启动记录及原始哈希在 `work/dictionary_builder_full_input_20261106/run_builder.launch.json`；终态、stderr、采样在同目录。最近进程扫描见 `work/dictionary_builder_terminal_auditor_20261106/handoff_process_observation.json`；只发现 Codex、shell 和 MCP 服务等进程，未发现此工程目录下运行的实验/监督进程。扫描范围及限制见 JSON。

## 恢复后的优先动作

1. **先诊断，不重跑长仿真**。检查 `tb_builder.sv:140,178-183` 中 `p_anonymous_namespace_graph_store_pool_used_s_o_ap_vld` 的捕获、`ap_done` 与测试平台在负边沿检查之间的时序，以及生成 builder 与父 `prepare.v` 对 `pool_used` 的数据/valid 连接。确认 `0` 是测试平台提前取值、连接/驱动问题、还是 RTL 实际错误；这是待验证假设，不是已确定原因。首字段成功描述符预期 `values=[512,773272,3]`、`table=[0,8,64]`，预期 used=2,320,328 bits。
2. 优先用独立、小型、确定性的有针对性测试或离线时序分析核实根因；保留当前失败原样。若需要修复测试平台，使用新的运行目录与新启动/终态记录，保留全尺寸输入和原有12 GiB进程组RSS/72 GiB全局守卫，不以缩小数据冒充完整结果。不要使用原目录独占创建的日志名直接重跑。
3. 完整输入 `install_words.mem` 97,790,069 bytes 及其 SHA、四字段核验在 `fixture.json` 和 `fixture_review.json`；原程序同次读取 SHA 与来源均有记录。已有的 `work/dictionary_put_xsim_full_fields_20261106/reference.mem` 为20,054,016字节派生快照。两者应随工程保留；勿重建或重新读取历史超大 TV/trace 只为例行状态检查。
4. `work/dictionary_builder_full_coverage_v2_20261106/` 已准备并编译增强版，增加整个存储池字段外位检查；其 mask 已在 `work/dictionary_builder_mask_hdl_check_20261106/review.json` 做 1,179,648 字独立 HDL 对照，但增强版 **未执行完整构建器仿真**，且继承待诊断的 pool-used 检查。修复前不要把它当成最终可运行版本。`work/dictionary_builder_adapter_comparison_20261106/review.json` 是4,096请求的有限适配器对照，`work/dictionary_builder_adapter_negative_controls_20261106/review.json` 是两项指定错误注入；均非完整AXI等价或安装器证明。
5. 修复后仍需实际完整四字段仿真及独立终态/范围复核，接着完成完整安装器、原始 native 语料、路由QoR、物理实现、板卡和论文/交付等原始目标。目标前提、失败分母和资源约束不得降低。实体 U280 之前未发现，迁移/新环境应重新核实。

## 已保留且可直接复用

- `work/migration_pause_20261106/independent_review_v2.json`：先前 put_1 + 真实RAM的2,891,290写入日志功能通过及快照绑定；由于旧监督退出，模拟进程退出码不可取，且不是完整builder/install证据。
- `work/dictionary_builder_terminal_auditor_20261106/audit.py` 与 `test_audit.py`：终态审计模板；当前 terminal_review 已写入，脚本独占创建，不要覆盖。若创建新尝试应适配新目录并重新核验绑定。
- `work/dictionary_builder_full_input_20261106/compile_builder_attempt2.stdout`、`elaborate_builder_attempt2.stdout`：已完成的构建结果，原始源码列表在 `sources.list`。生成的 xsim 快照仅可在工具版本、相关源和路径均核实匹配时复用；新实验应保留自身可追溯的来源，不依赖旧 PID。
- 最新权威快照 `HANDOFF_20261106_ALL_METADATA_VALID_COVERAGE.json`、`experiments/critical_path_20261106_v292.json`、`work/current_research_claim_matrix_v292_20261106/matrix.json`。研究计划后来添加了本轮准备/运行/审查的条目，但当前正式matrix未因组件结果关闭任何gate。
