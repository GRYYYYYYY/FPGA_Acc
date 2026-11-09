# DieRoute 迁移交接：2026-11-07，用户要求暂停

本文件及 `work/migration_handoff_20261107/pause_receipt.json` 优先于此前运行清单中的 `running_not_accepted`。暂停研究探索和后台实验，等待用户恢复；不要自动启动、重新编译或复制启动实验。

## 当前后台任务

唯一核实的实验为 `work/dictionary_builder_full_capture_v3_20261107/` 四字段实际生成 RTL builder 仿真。资源监控 `run_builder.py` 和 4 个 XSim 进程均已 SIGSTOP，状态 T；CPU 计数暂停后不再增加。保留进程内存，没有终止进程，也没有重跑。暂停时总 RSS 约 0.78 GiB。

| 角色 | PID | /proc start_ticks |
| --- | --- | --- |
| Python 资源监控 | 3710767 | 1829055404 |
| XSim 启动器 / PGID | 3710818 | 1829055409 |
| loader | 3710835 | 1829055411 |
| XSim 主程序 | 3710854 | 1829055419 |
| xsimk | 3710864 | 1829055882 |

主机 `fpgaacc-1--5e8de292dbd1-gxc4guphhd`，boot ID `128d5727-3fab-471f-bc6f-87cf78639358`。会话句柄历史值 11195，只作线索，不能跨会话假定有效。PID 必须与 boot、启动时间、命令、cwd 同时核验，禁止拿历史 PID 直接发信号。

最新可见日志：`PROGRESS cycles=40000000 field=0 requests=439021 responses=439020`。这是最近一次日志采样，不是精确暂停周期。尚无 FIELD PASS、最终 PASS 或终态回执，不能判断完整四字段通过。xsimk 已累计约 488 CPU 秒。

Vivado MCP 会话列表为空。未发现其他本工程实验/监控进程；root 无 crontab，tmux 无会话，atq/screen 未安装。Codex、编辑器、Jupyter、MCP 服务及工程外代理监控属于基础服务，保留。检查范围是当前容器可见进程与上述入口，不代表所有远端主机。

## 同容器无重复计算地接续

在工程根目录先执行只读核验：

```bash
python3 -B work/migration_handoff_20261107/resume_existing.py
```

用户决定恢复后执行：

```bash
python3 -B work/migration_handoff_20261107/resume_existing.py --resume
```

脚本先核验所有进程身份和暂停状态，用 pidfd 防止误操作重用的 PID，先恢复资源监控再恢复仿真。任何核验失败都应停止并检查，不能据此自动重启。本次交接仅运行只读模式，未执行恢复。

继续观察原目录的 `run_builder.stdout`、`run_builder.samples.jsonl` 和 `run_builder.terminal.json`。保留原约束：单进程虚拟内存/进程组 RSS 12 GiB、cgroup 72 GiB、准入 52 GiB、HDL watchdog 10 亿周期。暂停会计入原 supervisor 的墙钟 elapsed_seconds；性能解释需扣除暂停区间，不能直接作运行时比较。

## 跨容器迁移的边界

SIGSTOP 仅保留当前容器的内存现场。归档、WDB 和 XSim 编译快照都不是已经验证的可移植运行时检查点；销毁旧容器会丢失本次未完成的仿真进度。要避免这约 488 CPU 秒被重复计算，请保留旧容器，稍后原位恢复；或在用户恢复后让此任务在旧容器完成，再迁移结果。当前没有实施进程内存迁移，不承诺跨容器零重算。暂停仍占内存，平台实例计费是否停止取决于平台。

轻量归档保存当前运行目录（含编译快照）、91 个已绑定 RTL 源文件、输入 fixture、参考 pool、短回归和终态审计脚本、关键研究指针、日志及哈希清单；它是交接补充包，不是整个工程/全部历史证据的备份。工程其余 `work/`、源代码、原始输入和历史研究材料仍需随工程保留，不能只复制此包后删除原工程。

路径依赖：工具链依旧位于 `/inspire/hdd/global_user/guoruiyuan-253208540291/Xilinx/`；载入 `Vitis/2022.2/settings64.sh`。现有运行目录中的 `install_words.mem` 为绝对符号链接，TB 实际读取相邻 `dictionary_builder_full_input_20261106/install_words.mem`。迁移后需要核验这些路径；不要直接重跑 `prepare.py`，它会重新生成文件且已有 symlink 会冲突。若原进程确实丢失，先记录未完成终态，再另建运行目录，保留原日志，复用已存 fixture 和参考数据；禁止覆盖旧结果或从零重新生成历史大 trace。

## 已有结论与下一步

1. 原长仿真 `work/dictionary_builder_full_input_20261106/` 因 TB 过早检查 used 捕获值，在字段 0 报 `used mismatch 0`，属于失败记录，不能抹去。XSim 在 `$fatal` 时也可能返回 0。
2. `work/builder_used_actual_regression_20261107/simulate.log` 已通过实际 builder 两次连续短调用，验证 done/valid 后应再等待下一上升沿捕获 used。v3 只在四字段检查前补 `@(posedge ap_clk);#1;`，保留原输入规模和全池检查；TB SHA-256 `7c531ee1f589b9f55f923698ddbb1044ef70ec71b2823f7b0512c9f9e0aa135a`。
3. v3 等待完成后执行：`python3 -B work/builder_capture_v3_terminal_audit_20261107/audit.py`。需依次有 FIELD 0/1/2/3 PASS、`PASS full pool outside-field check 1179648 words`、`PASS four full dictionary fields`、正常 finish/exit、无 Fatal/Error、退出码 0 且 guard_reason 为空，然后人工复核证据范围及源绑定。
4. 输入为原始安装的 5,752,357 个 64-bit word；参考池 1,179,648 word；91 个原 RTL 源绑定存于 `rtl_bindings.json`。不要缩减数据替代此轮，不要重跑已完成的短回归/接口对照/负控制。
5. 本实验仅验证实际 builder 组件，内部 HLS read responder 简化，不能替代完整 installer、原生 28,878 次调用、AXI 全链路或板卡证明。物理 U280 仍需重新核验，历史环境无卡。

研究权威入口：`experiments/research_plan.json` 的 `current_claim_matrix` 指向 `work/current_research_claim_matrix_v292_20261106/matrix.json`；关键路径 `experiments/critical_path_20261106_v292.json`。原 G1–G8 仍未全部闭合；本次交接不宣告研究完成。先读取本文件与暂停回执，再按当前权威指针继续，不从旧交接里的历史队列重启实验。
