# FPGA-Acc-PAR 首阶段代码

当前代码是五篇路线的第一阶段公共实现，重点验证 PersistRoute 的确定性事务语义和实验基础设施。它不是 VPR/RWRoute 的替代品，也不是论文性能结果；当前 RR 图是可控的二维合成 FPGA 资源图，用于先把正确性、冲突和复现协议写实。

## 已实现

- 64 B `FileHeader` / `ConnectionTask`、16 B `ResourceState` / `TimingSnapshot`；
- 确定性 directed graph search 和 negotiated-congestion 迭代框架；
- 串行 baseline 与批量投机 search；
- resource version、read/write set、固定提交序、冲突 replay；
- 路径连续性、occupancy、capacity 和重复运行 hash 校验；
- random/cross/hotspot 合成实验和 JSON/CSV 原始结果；
- 可由普通 g++ 测试的 HLS commit kernel；
- Vitis HLS 2022.2 `csim → csynth → cosim → export xo` 脚本。

注意：当前节点容量简化为“节点资源容量”，没有实现 VPR switch/segment、route tree、多 sink timing 和 UltraScale+ PIP。因此当前结果仅为开发回归，不得写成论文 speedup/QoR。

## Windows 本机运行

PowerShell 默认执行策略可能禁止 `.ps1`。无需修改系统策略，使用单次 bypass：

```powershell
cd C:\Users\20641\Desktop\FPGA_Acc\code
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\build.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\test_hls_cpp.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_smoke.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_conflict_sweep.ps1
```

单次运行示例：

```powershell
.\build\persist_route_sw.exe --width 24 --height 24 --connections 32 `
  --capacity 3 --pattern random --seed 1 --iterations 30 `
  --mode speculative --batch 4 --threads 4
```

程序约定：退出码 `0` 为合法成功，`2` 为运行完成但未得到合法 route，`1` 为输入/程序错误。失败结果仍由实验运行器保存。

## Vitis HLS（安装后运行）

在包含 Vitis 2022.2 环境变量的 shell 中：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\scripts\run_vitis_hls.ps1
```

脚本运行：

1. C simulation；
2. U280 `xcu280-fsvh2892-2L-e`、250 MHz目标的综合；
3. Verilog co-simulation；
4. 导出 `.xo`。

如果目标板不是 U280，先修改 `hls/run_hls.tcl` 的 `set_part`。没有 Vitis 时脚本明确退出，不伪造综合/Fmax/资源结果。

## 输出

`experiments/run_experiments.py` 每次创建新的时间戳目录：

```text
experiments/results/<suite>_<UTC>/
  manifest.json       # config和可执行文件SHA-256、主机/Python
  raw/*.json          # 每个重复的完整命令、结果、stderr
  runs.csv            # 所有重复
  summary.csv         # median、合法性、确定性、hash
```

`conflict_sweep.json` 是必须通过合法性/QoR校验的冲突扫描；`failure_stress.json` 故意设置不可布通/难收敛压力，只用于确认失败被保存，不能通过 `validate_results.py` 是预期行为。

## 代码结构

```text
include/fpga_acc/schema.hpp      公共schema
include/fpga_acc/router.hpp      软件router接口
src/router.cpp                   搜索、RRR、事务和验证
src/main.cpp                     CLI/JSON
tests/router_tests.cpp           单元与确定性测试
experiments/                     实验配置和运行器
hls/                             commit kernel、testbench、Tcl
scripts/                         构建/测试/实验入口
```

## 下一实现顺序

1. 用 VPR 9 `rr_graph.bin/xml` converter 替换合成图，同时保留合成压力测试；
2. 增加 edge/switch/segment/delay class 和真正的多 sink route tree；
3. 对齐 PathFinder/VPR cost、rip-up策略和 golden QoR；
4. 实现空间 footprint/历史冲突 scheduler，而非当前固定批次；
5. 将 search bucket/MultiQueue 与 persistent state 搬入 HLS；
6. 接 FPGAIF/RapidWright 的 UltraScale+ exporter/validator；
7. 再开展 TilePlace、RouteCast、DieRoute 和 FusionPAR 分支。

## 当前验证边界

| 项目 | 当前状态 |
|---|---|
| C++编译、单元测试 | 可立即运行 |
| 合成实验、JSON/CSV | 可立即运行 |
| HLS kernel普通C++ testbench | 可立即运行 |
| Vitis HLS csim/csynth/cosim | 代码已备；待安装 Vitis 2022.2 |
| Vivado RTL仿真/上板 | 尚无完整search RTL；后续实现 |
| VPR 9 / FPGAIF / RWRoute真实设计 | converter尚待实现 |
