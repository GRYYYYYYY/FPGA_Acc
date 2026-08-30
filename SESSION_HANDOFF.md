# Codex 项目交接存档

更新日期：2026-08-31（Asia/Shanghai）。

## 1. 新设备/新会话首先执行

将仓库克隆到新设备的 Linux 原生文件系统，不要假定原机器的
`/home/gry/workspace/FPGA_Acc`、Xilinx 安装路径、内核、swap 或板卡状态仍然成立。

新会话必须先完整阅读：

1. `AGENTS.md`
2. `SESSION_HANDOFF.md`（本文件）
3. `CODEX_CONTEXT.md`
4. `projects/实现状态.md`
5. `projects/真实数据与论文基线运行指南.md`

推荐开场指令：

> 请完整阅读 AGENTS.md、SESSION_HANDOFF.md、CODEX_CONTEXT.md、projects/实现状态.md 和 projects/真实数据与论文基线运行指南.md；验证 Git、OS/内核、Vitis/Vivado/Vitis HLS、XRT、目标 XPFM、磁盘、内存/swap 与物理板状态。PersistRoute 不重跑已完成的最终 hw_emu；从 TilePlace 的真实 VPR 前端、CPU golden 和 placement 合法性闭环开始。长时间 Vitis/Vivado 作业按 AGENTS.md 交给 vivado_monitor。

首次检查：

```bash
git status --short --branch
git log -3 --oneline --decorate
uname -a
free -h
swapon --show
df -h .
source <Vitis安装目录>/settings64.sh
source <XRT安装目录>/setup.sh
v++ --version
vivado -version | head
vitis_hls -version | head
xbutil --version
xbutil examine
find /opt/xilinx/platforms -name '*.xpfm' -print
```

如果新设备的版本或平台路径不同，先更新该设备工作区中的 `AGENTS.md`，再运行
任何 Xilinx 作业。只有 `xbutil examine` 真实发现目标卡后，才进入上板实验。

## 2. 总体位置

总目标是依次完成五个独立论文工程：

```text
PersistRoute → TilePlace → RouteCast → DieRoute → FusionPAR
```

PersistRoute 是第一篇工程，当前已经完成本机可完成的工程闭环与论文草稿：真实
VPR/FPGAIF 数据转换、production ABI、PathFinder/MultiQueue、HBM Search/Commit、
4 Search CU + 1 Commit CU、XRT host、逐 connection timing feedback、原生 VPR
回写检查、HLS/RTL 验证、U280 routed implementation、真实 RR graph 子集多轮
`hw_emu`、CPU 强基线、QoR/消融材料和 ACM/DAC LaTeX 草稿。

PersistRoute 仍缺物理 U280 的端到端 runtime、功耗/能耗和重复试验。这些是外部
硬件待补项，不应阻塞第二篇 TilePlace。不得把 C-model 或 `hw_emu` 墙钟时间写成
真卡加速比。

下一工程明确为 `projects/tileplace`。现有 TilePlace 只是最多 512 instances、64
pages 的确定性 HLS 骨架，只有 toy testbench；尚无真实 VPR 数据、CPU golden、
合法化、强基线、XRT host 或论文结果。

## 3. PersistRoute 最终冻结状态

源码与论文冻结提交链：

```text
8832cc0  Extend PersistRoute to heterogeneous timing cases
a11d429  Add route-tree-aware timing seeds
10856a2  Close spmv timing QoR with route-tree costs
```

最新正确性/QoR机制：

- timing oracle 使用 VPR 9 `AnalysisDelayCalculator`/Tatum，每轮反馈逐 connection
  setup criticality/slack，production `Task` ABI 保持 32 bytes；
- candidate-path read set 取代 explored-resource read set，避免大图出现大量伪冲突；
- tail serialization 在停滞后收窄 issue width，修复 `softmax` 的尾部合法化；
- route-tree upstream timing seed 对共享树节点加入 source-to-attachment 延迟代价，
  修复高 fanout `spmv` 的 CPD 失真；
- `spmv` 最终使用 Q8 weight 128，其余冻结案例使用 weight 0。

修正后的六案例原生 VPR 矩阵：

| Case | Rounds | WL delta | CPD delta | Tier |
|---|---:|---:|---:|---|
| diffeq | 22 | +4.427% | +0.579% | Balanced |
| frisc | 18 | +4.659% | +0.876% | Balanced |
| elliptic | 20 | +3.934% | +3.857% | Throughput |
| clma | 8 | +3.216% | +0.662% | Balanced |
| spmv | 21 | +7.770% | 0.000% | Throughput |
| softmax | 23 | +8.912% | +3.388% | Throughput |

六例全部 legal，3 例达到 Balanced（WL ≤ 5%、CPD ≤ 3%），全部 6 例达到
Throughput（WL ≤ 10%、CPD ≤ 5%）。几何平均 WL/CPD 增量为
`+5.466%/+1.550%`。核心证据：

```text
projects/persistroute/experiments/balanced_pathreads_corrected_matrix_2026-08-29.json
projects/persistroute/experiments/tree_timing_weight128_spmv_full_2026-08-29.json
projects/persistroute/experiments/tree_timing_weight_sweep_diffeq_2026-08-29.json
projects/persistroute/experiments/spmv_timing_rootcause_2026-08-29.json
```

CPU 强基线另有 4 VTR + 2 Titan23 + 4 Koios 共十案例；serial/16-worker 配对的
route/QoR 完全一致，whole-flow/route-stage 几何平均为 `1.046x/1.356x`。这只是
CPU baseline，不是 PersistRoute 硬件加速比。

## 4. PersistRoute 硬件证据

最终 tree-seed 源码在 U280 平台完成完整 `v++ hw`：

```text
source commit: 10856a2
target clock: 180 MHz
WNS/TNS: +0.016 ns / 0
WHS/THS: +0.005 ns / 0
setup/hold failing endpoints: 0 / 0
xclbin SHA-256: 323ddd9f3170b8dccc2e76b63661971671da691390ff70984b62ba338cf18c57
```

可提交证据：

```text
projects/persistroute/experiments/u280_treeseed_hw_2026-08-29.json
```

大型 xclbin/报告目录被 `.gitignore` 排除，不会随 GitHub 自动迁移。原机器保留：

```text
build/xclbin/hw/persistroute.xclbin
  e3ca2e6030aa5b65d07390492e8d7070fcf74cd29064318cc7139c3e3ea69743
build/xclbin/hw_pathreads_2026-08-29/persistroute.xclbin
  da64d4b413a1438d27714d5d0b1c0d7e607ca47365849b654873aa5db424447f
build/xclbin/hw_treeseed_2026-08-29/persistroute.xclbin
  323ddd9f3170b8dccc2e76b63661971671da691390ff70984b62ba338cf18c57
```

已完成的最终 `hw_emu` 不要重跑。真实 `diffeq` RR graph 子集已经覆盖四 Search
CU 同 wave 和两轮冲突消解，并与 HBM C-model 五类输出逐字节一致：

```text
projects/persistroute/experiments/accelerated_pathfinder_hw_emu_2026-08-26.json
```

## 5. TilePlace 的第一阶段任务

先完成真实前端与 CPU correctness，不要一开始就跑 HLS/Vivado：

1. 编译并运行当前 toy testbench，记录当前接口和确定性行为；
2. 从冻结的 VTR 9 placement 流中定义真实数据契约：block type、初始/参考坐标、
   fixed/region constraint、CLB/BRAM/DSP site、net/pin、timing criticality；
3. 实现流式/低内存 packer 和 manifest，保留原始输入 SHA-256、VPR commit、seed、
   channel width 与命令；
4. 实现不限 512-instance 的 CPU golden，包含异构 site 合法性、唯一占用、区域约束、
   macro/cascade 连续形状与确定性 tie-break；
5. 将输出写回 VPR placement，并以 VPR placement/route/analysis 做 fail-closed 检查；
6. 先用 `diffeq` 做首个真实闭环，再扩展 `frisc/elliptic/clma` 和 Koios/Titan23；
7. correctness 冻结后再设计 page decomposition、增量 net/timing cost、HBM layout、
   多 CU/XRT 和 U280 构建。

TilePlace 的强基线至少包括 VPR 9 placement；DREAMPlaceFPGA、AMF-Placer 在确切
commit、依赖、命令和相同后端 router 未冻结前只能标为 B1/B2。比较必须使用同一
输入/约束并经同一 router 报告 routed wirelength、CPD、合法性和端到端时间。

## 6. Git 与本地数据边界

远端仓库：

```text
https://github.com/GRYYYYYYY/FPGA_Acc.git
branch: main
```

新设备应以 `git log -1` 显示的最新 handoff 提交为准。不要使用
`git clean -fdx`/`git clean -Xfd`：它们会删除被忽略的 Vitis/Vivado、XSim、数据集
和本地实验存档。

GitHub 只包含源码、脚本、论文源文件和紧凑 JSON 证据，不包含：

- `projects/persistroute/build/` 下的 `.xo`、xclbin、Vivado 工程和报告；
- `projects/persistroute/host/.run/` 的 XRT/XSim 现场；
- `projects/persistroute/third_party/` 的 VTR/FPGA24/RapidWright 等下载内容；
- 大型 rr graph、网表、placement/route 工作目录；
- 生成的论文 PDF。

如需在新设备复现 PersistRoute，按 JSON 中的来源、版本和 SHA-256 重新下载/构建，
不要假定缺少被忽略目录表示实验从未完成。

## 7. 原机器状态与清理提醒

交接时原机器为 Ubuntu 22.04.5、kernel `5.15.0-190-generic`、Vitis/Vivado
2022.2、XRT 2.14.354，VMware 未透传 U280；当前没有 Vitis/Vivado/XSim 长作业。

专用 `/var/tmp/persistroute-vivado-16g.swap` 在最新构建后仍处于启用状态。Codex
尝试关闭时因 `sudo` 需要交互密码而未改变系统状态。原机器所有者应在终端执行：

```bash
sudo swapoff /var/tmp/persistroute-vivado-16g.swap
sudo rm /var/tmp/persistroute-vivado-16g.swap
swapon --show
```

执行前再次确认没有 Vivado/Vitis 长作业且 `free -h` 有足够 available memory。
