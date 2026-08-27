# Workspace Context

## 当前目标

建立五个独立的“FPGA 加速 FPGA 布局布线”论文工程，按 PersistRoute → TilePlace → RouteCast → DieRoute → FusionPAR 推进。当前优先完成 PersistRoute 的真实 VPR/FPGAIF 数据闭环、完整 MultiQueue、多 PE/HBM/XRT、RapidWright 回写和论文级强基线。

## 已确定原则

- ASIC 文献仅学习数据流、存储、调度、冲突处理和软硬件划分，不移植 ASIC P&R 问题模型。
- FPGA routing 算法以 PathFinder/VPR、RWRoute/RapidWright 等 FPGA 工作为依据。
- 五篇论文共享基础设施，但必须分别具有独立问题、算法机制、硬件机制和实验结论。
- 默认 Vitis/Vivado 2022.2 与 U280；FPGA24 按竞赛规定版本单独验证。
- 未获得可执行代码的工作只能作为 B2 文献基线，不声称直接复现。

## 本轮完成

- 在 `projects/persistroute/tools` 实现 VPR `rr_graph.xml`、`.place`、`.route` connection 转换，输出带 SHA-256 manifest 的确定性 XRT ABI 数组。
- 实现 8-bank 完整二叉堆 MultiQueue，以及工作数组、队列和事务日志外置 HBM 的 `search_hbm_kernel`。
- 实现动态规模 `commit_hbm_kernel`、resource version 检查、确定性提交和冲突重放。
- `Task` ABI 扩展为 32 bytes并携带稳定 `net_id`；同一多 sink net 可以共享 route-tree trunk，不同 net 才产生容量冲突。
- 实现四 search CU + 一 commit CU 的 U280 HBM connectivity 和 XRT native host；host 记录输入、设置、路由/重放、输出及总时间。
- 实现 RapidWright Java bridge：读取 DCP 或 FPGA Interchange，导出 nodes/PIPs/connections/已有路由；验证并回写 PIP 到 DCP 和 `.phys`。
- 实现 RapidWright CSV → HLS 图和硬件 node path → RapidWright PIP CSV 的严格可逆转换。
- 实现 Vitis HLS csim/csynth/cosim 与 `v++` xclbin 构建入口。
- 实现 VPR serial/parallel、RWRoute、CUFR、Vivado 的可审计强基线 runner、Vivado QoR Tcl 与 QoR parser；B0/B1/B2 明确分级。
- 新增真实运行指南、论文基线覆盖矩阵、工具探测和实现状态文档。
- 新增直接消费 production ABI 的确定性 PathFinder 控制层与 CLI：完成多轮 present/history 更新、按 net rip-up、未受影响树跨轮持久化和多 sink trunk 共享，并输出逐轮审计记录。
- 将上述控制层接入四个 `search_hbm_kernel` CU 与一个 `commit_hbm_kernel` CU 的 XRT host；支持同轮并发搜索、允许协商式暂时超用、确定性提交、按过用 net rip-up 和跨轮重路由。
- 将 VPR 9 `AnalysisDelayCalculator`/Tatum STA 作为 host timing oracle 接入 CPU、HBM C-model 与 XRT 控制层；每轮以当前 connection RR path delay 覆盖 `net_delay`，反馈 setup criticality/slack，保持 32-byte Task ABI 不变。完整真实 `diffeq` CPU 与 4-PE HBM C-model 均已闭环合法收敛。
- 增加 timing-aware 最少 reroute 轮次和 `(criticality desc, priority, task_id)` 确定性调度。统一 base cost 64/最少 3 轮策略下，真实 `frisc` 与 `elliptic` 4-PE HBM C-model 的 CPD 相对 VPR 分别为 +0.803%/+0.499%，均 0 overuse；两案例各自两次运行六类核心输出逐字节一致。
- 在本机 Vitis/Vivado 2022.2 上完成五个 top 的独立 HLS 工程：全部通过 C 仿真和 Verilog/XSIM RTL 协同仿真，并导出五个 `.xo`；修正 HLS 动态指针协仿深度、外存数组读改写和 MultiQueue 分银行退化问题。
- 对两个 production top 的 HLS RTL 完成 Vivado 2022.2 OOC 综合、优化、DRC、时序/资源报告和 DCP 导出；4 ns 约束下 search WNS 为 +0.427 ns，commit WNS 为 -0.694 ns，后者明确保留为待优化问题。

## 验证结果

`projects/build_all.ps1` 和 `projects/test_all.ps1` 已接入 PathFinder testbench；当前 Linux 机器无 PowerShell/CMake，新增部分已用等价 `g++ -std=c++17 -Wall -Wextra -Wpedantic` 命令验证，并通过 production packer 固定样例的 CLI 端到端测试。既有五工程、转换器、静态 ABI 和强基线 runner 仍由普通 g++/Python 回归。

当前机器已确认 Vitis HLS/v++ 2022.2、Vivado/XSIM 2022.2、XRT 2.14.354 与 `xilinx_u280_gen3x16_xdma_1_202211_1` 平台可用；XPFM、hw XSA、平台版本、DKMS 和软件包哈希记录在 `projects/persistroute/experiments/environment_2022_2_u280.json`。该机器是未透传 U280 PCIe 的 VMware 虚拟机，因此 `xbutil examine` 正常返回 0 块设备，不能在本机宣称上板通过。四 search CU + 一 commit CU 的 U280 `hw` 已完成 system link、32 端口 HBM block design、综合、placement、routing、bitstream 与 xclbin 打包；180 MHz 下最终 WNS `+0.016 ns`、TNS `0`、WHS `+0.006 ns`、THS `0`，证据见 `projects/persistroute/experiments/vitis_link_2022_2_u280.json`。同一多 CU 系统的 `hw_emu` xclbin、XSim 与 XRT native host 已通过，tiny production-ABI 输出与 C++ golden 逐字节一致，证据见 `projects/persistroute/experiments/hw_emu_2022_2_u280.json`。加速 PathFinder 又在真实 `diffeq` RR graph 子集上完成两项 RTL 终验：4 个 Search CU 同 wave 的 4-task 用例一轮合法结束；2-task 冲突用例从首轮 1 个超用资源经 rip-up/re-route 在第二轮降为 0。两项均退出码 0、`legal=true`、`golden_match=true`，五类输出与 HBM C-model 逐字节一致，XSim 无 ERROR/FATAL，证据见 `projects/persistroute/experiments/accelerated_pathfinder_hw_emu_2026-08-26.json`。VPR 9 已完成四个标准案例及 Titan23/Koios 代表案例的 serial/parallel B0 配对。RapidWright 2022.2.0-beta/JDK 11 已安装；FPGA24 v1.8 `logicnets_jscl` 的官方 DeviceResources/NXRoute 已真实运行，bridge 完成 6-PIP 非空回写与逐字节重提取；Vivado 2022.2 又完成 27961/27961 个 routable nets 的全设计布线，0 routing errors、0 DRC violations。CUFR `ea4b031...` 和官方 RWRoute `f86cb487...` 均在同一 VM/输入上合法收敛且通过官方 checker；CUFR/RWRoute 分别为 26.33/35.59 s、critical-path wirelength 234/217、score 47.097/53.731。官方输入无用户时序约束，因此 Vivado 结果只证明布线合法，不证明时序收敛。证据见 `projects/persistroute/experiments/fpga24_logicnets_jscl_2026-08-24.json`、`projects/persistroute/experiments/cufr_logicnets_jscl_2026-08-24.json` 与 `projects/persistroute/experiments/rwroute_logicnets_jscl_2026-08-24.json`。

## 关键文件

- `projects/persistroute/README.md`：PersistRoute 生产/回归架构和命令。
- `projects/persistroute/src/search_hbm.cpp`、`commit_hbm.cpp`：生产 HBM kernels。
- `projects/persistroute/host/multi_pe_xrt_host.cpp`：多 CU XRT host。
- `projects/persistroute/connectivity.cfg`、`build_xclbin.ps1`：U280 HBM/xclbin 构建。
- `projects/persistroute/rapidwright`：DCP/FPGAIF 导出与回写。
- `projects/persistroute/tools`：VPR、RapidWright 与 XRT ABI 转换器。
- `projects/experiments/strong_baselines`：论文强基线运行和 QoR 解析。
- `projects/真实数据与论文基线运行指南.md`：安装软件后的完整流程。
- `projects/实现状态.md`：已验证、待工具验证和后续研究实现边界。

## 当前下一步

1. PersistRoute 已冻结 4 个 VTR、2 个 Titan23 和 4 个 Koios 案例的 1-worker/16-worker CPU 基线；全部配对 route/QoR 一致，whole-flow/route-stage 几何平均加速为 `1.046x/1.356x`。论文草稿、claim matrix、实验计划、CSV、LaTeX 和 SVG 位于 `projects/persistroute/paper/`。
2. PersistRoute 仍缺物理 U280 的端到端 runtime、能耗、重复试验，以及其余七个学术案例的完整 QoR；当前 VM 无卡，不能用 `hw_emu` 替代。VPR route 写回/原生验证已完成，`frisc`/`elliptic` CPD 增量为 +0.884%/+0.549%，但 wirelength 增量 +3.656%/+3.864% 未达到 2% 门槛。下一本机工程项是优化 wirelength 策略并扩展 timing-priority 矩阵。
3. 若不等待外部硬件，开始 TilePlace 的真实 VPR/FPGAIF 前后端。高容量资源多 owner、图模板压缩和高于 180 MHz 的优化保留为 PersistRoute 后续增强。
4. 如论文验证矩阵确实需要，可新增 timing-mode RTL 小子集终验；不要重跑既有最终 hw_emu。

## Windows → Ubuntu VM 续接

- 移动或共享 `FPGA_Acc` 工程目录只会转移代码、报告和本文件，不会自动转移 Codex 原生会话历史。
- 在 Ubuntu Codex 中打开 Linux 可见的工程路径后，先要求其完整阅读 `AGENTS.md`、`SESSION_HANDOFF.md`、`CODEX_CONTEXT.md`、`projects/实现状态.md` 和 `projects/真实数据与论文基线运行指南.md`，即可从当前技术状态继续新任务。
- 不建议直接复制整个 Windows `C:\Users\20641\.codex` 到 Linux `~/.codex`：其中可能包含认证、全局配置、数据库和 Windows 绝对路径；官方可支持的跨系统本地 session 导入方式尚未确认。
- VMware 共享目录适合作为传输目录。Vitis/Vivado/XRT 的正式构建建议把工程复制到虚拟机原生 ext4 目录，避免共享文件系统的权限、符号链接、大小写和 I/O 性能问题。
