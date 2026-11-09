# DieRoute 恢复入口：独立文献更新稿和源码编译复核 — 2026-10-30

原目标未完成。历史要求见 `HANDOFF_20261021.md`。当前矩阵v169/314条记录，关键路径 `experiments/critical_path_20261030_v169.md`；以 `experiments/research_plan.json` 当前指针为准。原11语料/311096搜索、45正式槽、预算及八门槛保持，所有门槛仍开放。

新增可审阅稿：`work/related_work_thesis_paper_update_20261030/paper/dieroute.pdf`，32页。它从冻结22October评测快照独立派生，仅六处日期/范围、相关工作表述/归属和引文范围修改，逆变换逐字恢复父TeX；其他编译输入及图表保持。首页与摘要明确评测日期22October、文献更新30October，因此不能把此稿作为最新全部实验结果或最终论文。

新增段落涵盖作者学位论文的部分路由、criticality/共享、冲突网选择性修复、逐步扩框和局部STA时序隔离条件，并明确区分期刊文章正文尚未审阅。文献来源和页码/文本行号/SHA证据仍见 `work/rwroute_thesis_extended_methods_review_20261030` 及不变的 `HANDOFF_20261030_LITERATURE.md`。

编译exit0，无未解析引文/引用或overfull hbox；新文本及父稿八个数值标记检查通过。页1/2/32已渲染并肉眼核对，无观察到的裁切或重叠。相关记录为 `build_review.json`、`visual_review.json` 和 `literature_update_manifest.json`。

源码包 `dieroute_literature_draft_sources.tar.gz` 有96个绑定编译输入（含build.sh及预渲染图）。已经在 `relocated_verification` 目录实际解包、验证SHA、在没有旧PDF的条件下重新编译，32页PDF全文提取结果逐字相同。此项仅证明文档编译搬迁，不证明图生成、实验复现或完整研究artifact已通过；见 `relocated_build_review.json`。

并行任务仍以实际句柄核验：7仿真、2终态监控、2后续队列。句柄、资源守卫和观察路径详见 `HANDOFF_20261030_RTL.md`；共享可更新记录仍在CSR根目录 `latest_all_jobs_verified_wait.json`。三个候选完整安装和全28878正向审计尚未证明，之后才可执行负向观察器测试。不得因静默重启、修改watchdog或改活动绑定源。

负向执行脚本路径和前置条件见 `HANDOFF_20261030_LITERATURE.md`。后续独立工作仍包括原研究制品的依赖/传递来源审计，以及完整文献和创新性对比；本源码包不替代它们。完整语料、所有失败及正式45分母保持。U280仍无实卡可用，无实卡速度/能耗、平台fit或300MHz达标结论。
