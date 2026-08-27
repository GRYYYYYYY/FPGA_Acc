# PersistRoute 独立工程

本工程包含两套实现：

- `search_kernel/commit_kernel`：固定上限的片上工作区版本，用于快速 C++/HLS 回归；
- `search_hbm_kernel/commit_hbm_kernel`：论文实验用生产版本，真实 RR graph、工作数组、完整 8-bank MultiQueue 和事务日志位于 HBM，图规模采用 32-bit 索引。
- `pathfinder.cpp/pathfinder_host.cpp`：直接消费同一生产 ABI 的确定性 negotiated-congestion 控制层，负责多轮 present/history 更新、按 net rip-up 和持久多 sink route tree；无需 AMD 工具即可回归。
- `accelerated_pathfinder.cpp`、`hbm_cmodel_backend.cpp` 与两个 `accelerated_*_host.cpp`：在相同控制语义下分别驱动 HBM C-model 和 4-search-CU + 1-commit-CU XRT backend，并输出可逐轮比对的审计哈希。

生产数据流为：

1. VPR：`rr_graph.xml + .route -> ConnectionTask CSV -> XRT ABI arrays`；
2. RapidWright/FPGAIF：`DCP/.phys -> nodes/pips/connections -> XRT ABI arrays`；
3. 四个 XRT search CU 基于同一轮持久资源快照投机搜索；
4. host 按 `(priority, task_id)` 合并事务，单一 HBM commit CU 确定性提交；
5. 冲突 connection 在新版本状态上重放；
6. 商业图路径通过 edge catalog 反解为 PIP CSV，由 RapidWright 回写 DCP/FPGAIF，最后交 Vivado 验证。

普通 C++ 回归：

```powershell
..\build_all.ps1
..\test_all.ps1
```

在 Linux 上可单独构建并运行 production-ABI PathFinder host：

```bash
make -C host persistroute_pathfinder
./host/persistroute_pathfinder work/vpr_input work/routed
```

它输出 `routed.paths.csv`、`routed.route_trees.csv`、`routed.iterations.csv`、
`routed.resources` 和 `routed.pathfinder.json`。路径 CSV 与 RapidWright PIP 反解工具使用相同格式。
`PERSISTROUTE_MAX_ITERATIONS`、`PERSISTROUTE_PRESENT_START_Q`、
`PERSISTROUTE_PRESENT_MULTIPLIER_Q` 和 `PERSISTROUTE_HISTORY_INCREMENT_Q` 控制 PathFinder 轮次与 Q8 代价更新。
启用 timing analyzer 时，`PERSISTROUTE_MIN_TIMING_ITERATIONS`（默认 1）规定在允许零超用终止前至少执行多少个完整路由/STA 轮次；大于 1 时，每次 STA 更新后全网进入下一轮 reroute，使新 criticality 实际影响路径选择。
每次 STA 更新还会按 `(criticality desc, priority, task_id)` 重新确定 connection 和 net 的下一轮顺序；固定 tie-break 保持重复运行确定性。

真实逐 connection timing 更新通过 host callback 接入，production `Task` ABI 仍保持 32 bytes。每轮 Search/Commit 后，host 将当前路径的 RR delay 写成
`<output>.timing_iteration_N.input.csv`，外部 analyzer 必须返回每个 task 的 setup criticality、slack 和全设计 CPD；校验通过的 `criticality_q` 会用于下一轮 CPU 或 HBM/XRT Search。逐轮摘要写入 `<output>.timing_iterations.csv`。不设置 `PERSISTROUTE_TIMING_COMMAND` 时维持原有固定 criticality 行为。

VPR 9/Tatum analyzer 的可复现接入方式：

```bash
cd /path/to/vtr-9.0.0-src
patch -p1 < /home/gry/workspace/FPGA_Acc/projects/persistroute/tools/vpr_timing_export.patch
cmake --build build_vpr --target vpr -j2

export PERSISTROUTE_TIMING_COMMAND="python3 /home/gry/workspace/FPGA_Acc/projects/persistroute/tools/vpr_timing_analyzer.py"
export PERSISTROUTE_VPR_BIN=/path/to/vtr-9.0.0-src/build_vpr/vpr/vpr
export PERSISTROUTE_VPR_ARCH=/path/to/architecture.xml
export PERSISTROUTE_VPR_CIRCUIT=/path/to/design.blif
export PERSISTROUTE_VPR_NET=/path/to/design.net
export PERSISTROUTE_VPR_PLACE=/path/to/design.place
export PERSISTROUTE_VPR_ROUTE=/path/to/original-legal-design.route
export PERSISTROUTE_VPR_CHAN_WIDTH=200
./host/persistroute_accelerated_cmodel work/vpr_input work/timing_routed
```

补丁只在 VPR analysis 的 `net_delay` 矩阵上覆盖本轮 PersistRoute connection delays，再由真实 packed netlist、atom timing graph 和约束运行 Tatum STA；原始 `.route` 只用于初始化和合法的 net/pin 映射。当前 oracle 支持 clustered routing，不支持 `--flat_routing`。`pack_hls_inputs.py` 的 edge delay 使用 VPR buffered local `T_linear` RC 模型并量化为 ps；pass switch 使用局部 RC 近似。

最终 route tree 可写回并交 VPR 原生检查。回写器从原始 `.route` 保留 placement ID、net/pin 描述和 sink pin index，从 RR graph 恢复每条树边的 switch，并验证树的唯一父节点、连通性、terminal sinks 和 edge adjacency：

```bash
python3 tools/write_vpr_route.py original.route rr_graph.xml connections.csv \
  routed.route_trees.csv routed.route
python3 tools/validate_vpr_route.py --vpr /path/to/vpr --arch arch.xml \
  --circuit design.blif --net design.net --place design.place \
  --route routed.route --rr-graph rr_graph.xml --channel-width 200 \
  --work-dir work/vpr_native_validation
```

验证器先要求 route header 的 Placement ID 等于 `.place` 文件 SHA-256，再在私有工作目录运行 VPR `--analysis`；只有 route load、routing consistency、feasibility、wirelength、CPD 和 VPR 退出状态全部成功才报告 `legal=true`。
`pack_hls_inputs.py --channel-length-cost-q N` 可在不改变 ABI 的前提下给进入 CHAN RR node 的 edge 增加 `N * (length - 1)` 静态代价；默认值为 0，保持旧输入逐字节语义。该选项是消融旋钮，不是推荐策略：`frisc` 的 16/64 两个试点都使 VPR-native wirelength 恶化。

Vitis 2022.2/U280 构建：

```bash
./run_hls.sh
./run_vivado_ooc.sh
./build_xclbin.sh \
  /opt/xilinx/platforms/xilinx_u280_gen3x16_xdma_1_202211_1/xilinx_u280_gen3x16_xdma_1_202211_1.xpfm hw
```

也可在 PowerShell 中运行：

```powershell
.\build_xclbin.ps1 -Platform D:\xilinx\platforms\xilinx_u280_gen3x16_xdma_1_202211_1.xpfm
```

`run_hls.sh` 可接受 `search_legacy`、`search_hbm`、`scheduler`、`commit_legacy`、`commit_hbm` 之一以单独回归。`run_vivado_ooc.sh` 对两个 production top 的 HLS RTL 做 Vivado out-of-context 综合并保存 DCP、时序、利用率和 DRC 报告。Vitis HLS/XSIM 实测结果与 XO 哈希保存在 `experiments/hls_2022_2_u280.json`；旧版 Vivado OOC 结果与 DCP 哈希保存在 `experiments/vivado_ooc_2022_2_u280.json`，它早于本轮 AXI bundle 合并。Vitis/XRT/U280 平台的精确版本、路径和哈希见 `experiments/environment_2022_2_u280.json`。本机无 U280 PCIe 透传，因此不包含上板结果。

XRT host 建议在安装了 XRT 与板卡驱动的 Linux 主机编译：

```bash
cd host
make
./persistroute_multi_xrt ../build/xclbin/hw/persistroute.xclbin input_prefix output_prefix
```

`PERSISTROUTE_PE_COUNT`、`PERSISTROUTE_QUEUE_DEPTH`、`PERSISTROUTE_TX_CAPACITY`、
`PERSISTROUTE_MAX_REPLAY` 可控制 PE 数、每个 heap bank 深度、事务池容量和重放上限。
所有正式实验必须保存转换 manifest、xclbin hash、host JSON、回写报告和 Vivado QoR 报告。

`persistroute_pathfinder` 是普通 C++ correctness/control reference；`persistroute_accelerated_cmodel`
和 `persistroute_accelerated_xrt` 分别执行同一控制层的 HBM C-model 与多 CU XRT backend。真实 VPR
RR graph 子集上的 4-CU 单 wave 和两轮冲突重路由 `hw_emu` 已与 C-model 五类输出逐字节一致，证据见
`experiments/accelerated_pathfinder_hw_emu_2026-08-26.json`。本机无 U280 PCIe 透传，因此该结果是 RTL
集成功能证据，不是实际上板或性能证据。
