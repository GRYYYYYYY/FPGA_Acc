# Codex 新会话交接存档

更新日期：2026-08-27（Asia/Shanghai）。

## 1. 新会话首先执行

工作目录固定为：

```text
/home/gry/workspace/FPGA_Acc
```

新会话应先完整阅读以下文件，再继续任何实现或实验：

1. `AGENTS.md`
2. `SESSION_HANDOFF.md`（本文件）
3. `CODEX_CONTEXT.md`
4. `projects/实现状态.md`
5. `projects/真实数据与论文基线运行指南.md`

推荐的新对话开场指令：

> 请先完整阅读 AGENTS.md、SESSION_HANDOFF.md、CODEX_CONTEXT.md、projects/实现状态.md 和 projects/真实数据与论文基线运行指南.md，验证 Git/环境状态，然后从 PersistRoute 论文包复核与下一工程 TilePlace 的真实前端接入继续。长时间 Vitis/Vivado 作业按 AGENTS.md 交给 vivado_monitor，不要重跑已经完成的最终 hw_emu。

## 2. 当前总体位置

总目标是依次完成五个独立论文工程：PersistRoute → TilePlace → RouteCast → DieRoute → FusionPAR。

第一个工程 PersistRoute 的代码、实现、功能验证和论文材料包已收尾：真实 VPR/FPGAIF 前端、production ABI、PathFinder 控制、MultiQueue、HBM Search/Commit、多 CU XRT、真实 timing feedback、HLS/RTL 验证、U280 完整实现、真实 VPR 子集多轮 `hw_emu`、十案例 CPU 基线和论文图表均已具备。

原先第一项未完成任务“将 PathFinder 控制层接入四 Search CU + Commit CU，并与真实 VPR RR graph 做逐轮 golden 对照”已于 2026-08-26 完成。

当前边界与下一项是：

1. PersistRoute 的物理 U280 端到端性能、能耗、重复试验和消融仍需有卡环境完成；当前 VM 不能形成这些 claim；
2. 论文材料入口为 `projects/persistroute/paper/README.md`，十案例冻结结果为 `paper/generated/paper_results.json`；
3. `frisc` 与 `elliptic` timing-priority HBM C-model 已用统一策略进入 2% CPD 门槛，且完整 VPR route 写回/原生验证已通过；原生 wirelength 增量 +3.656%/+3.864% 尚未达到 2% 门槛。两点静态 channel-length edge-cost 消融均使 wirelength 恶化，不能冻结。若继续 PersistRoute，下一项是共享 route-tree/合法后 cleanup 策略并扩展其余七案例 QoR；否则可进入第二个工程 TilePlace 的真实 VPR/FPGAIF 前端。

不要把 `hw_emu` 墙钟时间当作上板性能，也不要宣称当前 VM 已实际上板。

## 3. 最新功能终验结果

最终证据：

```text
projects/persistroute/experiments/accelerated_pathfinder_hw_emu_2026-08-26.json
```

使用完整真实 VTR 9 `diffeq` RR graph（32920 nodes、344820 edges），以固定 task ID 选择代表 connection 子集控制 XSim 时间：

- 4-CU 并发用例：task IDs `0, 7, 11, 13`；单 wave 发射 4 个 Search，1 iteration、4 searches、0 overuse；host exit 0，`legal=true`、`golden_match=true`；墙钟 38:44.44，峰值 RSS 648692 KiB。
- 两轮冲突用例：task IDs `1901, 1903`；第一轮 1 个 overused resource，Commit 后 rip-up/re-route，第二轮降为 0；2 iterations、4 searches；host exit 0，`legal=true`、`golden_match=true`；墙钟 59:03.91，峰值 RSS 647504 KiB。
- 两组的 `.paths.csv`、`.route_trees.csv`、`.iterations.csv`、`.accelerated_iterations.csv` 和 `.resources` 均与 HBM C-model 逐字节一致。
- 两次 XRT 均报告 `All the simulator processes exited successfully`，XSim 的实际 `ERROR/FATAL` 计数均为 0。
- 静态接口审计通过。

本地结果目录（被 Git 忽略，但仍保留在磁盘）：

```text
projects/persistroute/experiments/accelerated_pathfinder_2026-08-25/vpr_subset/hw_emu_final_parallel4
projects/persistroute/experiments/accelerated_pathfinder_2026-08-25/vpr_subset/hw_emu_final_conflict2
projects/persistroute/host/.run/275747
projects/persistroute/host/.run/284123
```

先前运行约 4 小时的 `diffeq_issue4_round2` 并非算法报错，而是交互执行会话中断；它没有最终 JSON。不要把它写成失败的 RTL 结果，也无需重跑。最终两个可控用例已覆盖 4-CU 同 wave 和多轮协商式冲突消解。

## 4. 已完成的关键技术状态

- production `Task` ABI 为 32 bytes，保留稳定 `net_id`；相同 net 支持多 sink route-tree trunk 共享。
- `search_hbm_kernel` 使用 HBM 工作数组和完整 8-bank MultiQueue。
- `commit_hbm_kernel` 支持确定性提交和 negotiated-congestion 的暂时超用。
- `accelerated_pathfinder.cpp` 是复用控制层；HBM C-model 与 XRT backend 使用相同控制语义。
- 完整真实 `diffeq` HBM C-model 已完成 1973/1973 tasks，23 iterations 后 0 overuse，重复运行输出一致。
- host-side VPR 9/Tatum timing oracle 已接入 CPU、HBM C-model 和 XRT 控制层：每轮按当前 RR path delay 运行真实 timing graph STA，并反馈逐 connection setup criticality。采用本轮 RC delay 模型后，完整 `diffeq` CPU 为 3 轮/CPD 7.164 ns，4-PE HBM C-model 为 12 轮/CPD 7.274 ns，均 0 overuse、`legal=true`；证据见 `projects/persistroute/experiments/timing_criticality_2026-08-26.json`。
- timing oracle 现可强制最少 reroute 轮数，并在 STA 后按 criticality 降序确定性重排。统一 base cost 64、最少 3 轮策略下，`frisc` 与 `elliptic` 4-PE HBM C-model 相对 VPR CPD 分别为 +0.803%/+0.499%，均 0 overuse；两案例各自两次运行六类核心输出逐字节一致，证据见 `projects/persistroute/experiments/timing_priority_{frisc,elliptic}_2026-08-27.json`。
- Search 和 Commit HLS csim/csynth/Verilog cosim 均通过。
- 4 Search CU + 1 Commit CU 的 U280 `hw` 完整实现已完成；180 MHz routed timing 为 WNS `+0.016 ns`、TNS `0`、WHS `+0.006 ns`、THS `0`。
- 当前 `hw_emu` xclbin SHA-256：`73ff9d105a486c2f8cfa73e002756343947aa6d29d9b1fdd4e3523521f75cc33`。
- FPGA24 `logicnets_jscl`、Vivado 全设计合法布线、CUFR 和 RWRoute 强基线已有真实证据，详见各 experiment JSON。

关键源码：

```text
projects/persistroute/src/accelerated_pathfinder.cpp
projects/persistroute/src/hbm_cmodel_backend.cpp
projects/persistroute/src/search_hbm.cpp
projects/persistroute/src/commit_hbm.cpp
projects/persistroute/host/accelerated_xrt_host.cpp
projects/persistroute/include/accelerated_pathfinder.hpp
```

## 5. Xilinx 环境与硬件边界

当前已核实：

```text
OS: Ubuntu 22.04.5 LTS
Kernel: 5.15.0-190-generic
Vitis/Vivado/Vitis HLS: 2022.2
XRT: 2.14.354
U280 platform: /opt/xilinx/platforms/xilinx_u280_gen3x16_xdma_1_202211_1/xilinx_u280_gen3x16_xdma_1_202211_1.xpfm
```

运行 Xilinx 命令前必须执行：

```bash
source /tools/Xilinx/Vitis/2022.2/settings64.sh
source /opt/xilinx/xrt/setup.sh
```

VMware 未透传物理 U280，`xbutil examine` 返回 0 devices 是预期结果。论文当前不要求实际上板；HLS/RTL 仿真、`hw_emu` 和实现报告是当前完成门槛。

当前 swap 状态只有 `/swapfile` 2 GiB（约 0.8 GiB 已用）。此前 16 GiB `/tmp/persistroute_vivado.swap` 是临时文件，重启后未启用。若未来重新运行内存密集的 `v++ hw`/Vivado 实现，必须先复核 `free -h` 与 `swapon --show`，不要假定额外 swap 存在。

## 6. 长作业代理配置

按 `AGENTS.md`：

- 主代理用于架构、算法、诊断、代码修改和报告解释；目标配置为 `gpt-5.6-sol` high。
- Vitis HLS、Vivado 综合/实现、`v++` link、routing、bitstream 等长作业交给项目自定义代理 `vivado_monitor`。
- `vivado_monitor` 使用 `gpt-5.6-terra` medium；必须给出精确命令、工作目录、预期输出和完成标准，并要求等待真实退出状态。
- 快速环境检查、短报告读取不需要监控代理。

## 7. GitHub 与本地 Git 状态

私有仓库：

```text
https://github.com/GRYYYYYYY/FPGA_Acc
```

当前配置：

```text
branch: main
remote: origin -> https://github.com/GRYYYYYYY/FPGA_Acc.git
GitHub CLI account: GRYYYYYYY
```

建立交接文档前的基础提交为 `38b9afd`。本文件提交后应以最新 `git log -1` 为准。

根级 `.gitignore` 排除了 Vitis/Vivado 生成物、XSim `.run`、第三方下载仓库、论文 PDF、真实数据工作目录和二进制产物。`.gitignore` 不会删除文件，但这些文件也没有 GitHub 备份。

当前本地被忽略的大目录约为：

```text
projects/persistroute/build       611 MiB
projects/persistroute/host/.run   3.1 GiB
projects/persistroute/third_party 962 MiB
projects/persistroute/experiments 2.8 GiB
论文库                            26 MiB
```

禁止使用 `git clean -fdx` 或 `git clean -Xfd`，它们会删除被忽略的本地实验存档。新会话不要因为目录被 `.gitignore` 排除而清理或重建它们。

常规提交：

```bash
git status
git add <明确文件>
git commit -m "说明"
git push
```

## 8. 新会话快速验证清单

```bash
cd /home/gry/workspace/FPGA_Acc
git status --short --branch
git log -1 --oneline --decorate
uname -r
swapon --show
source /tools/Xilinx/Vitis/2022.2/settings64.sh
source /opt/xilinx/xrt/setup.sh
v++ --version
xbutil --version
python3 -m json.tool projects/persistroute/experiments/accelerated_pathfinder_hw_emu_2026-08-26.json >/dev/null
python3 projects/persistroute/tools/static_interface_audit.py
```

正常预期：Git 工作树干净、内核为 `5.15.0-190-generic`、Vitis 2022.2、XRT 2.14.354、实验 JSON 语法通过、静态接口审计 PASS。

## 9. 当前没有运行中的长作业

最终两个 `hw_emu` 已自然退出并归档，当前无需恢复、attach 或等待任何 host/XSim/Vivado 进程。十案例 CPU 基线与论文图表也已冻结；新会话可以从论文包复核或 TilePlace 开始。
