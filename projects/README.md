# 五篇论文的五个独立工程

| 工程 | 论文 | 当前可综合顶层 | 独立科学边界 |
|---|---|---|---|
| `tileplace` | TilePlace | `tileplace_kernel` | 时序异构页分配与确定合法位置 |
| `routecast` | RouteCast | `routecast_kernel` | FPGA RR语义增量routing sketch |
| `persistroute` | PersistRoute | `search_kernel`, `commit_kernel` | 路由搜索、版本事务与确定提交 |
| `dieroute` | DieRoute | `dieroute_kernel` | SLL预留、shadow版本和die队列映射 |
| `fusionpar` | FusionPAR | `fusionpar_kernel` | 原子move-route-repair共享状态协议 |

五个目录不引用彼此头文件或源码，每个都能独立复制、构建和归档。PersistRoute
已完成真实 VPR/FPGAIF、强软件 baseline、HLS/RTL、U280 routed implementation 和
论文材料闭环，但仍缺物理板 runtime/能耗。

截至 2026-10-04，TilePlace 已建立真实 VPR placement 前端、CPU golden、写回合法性与
native 回归；input-union 基线已通过四事务/五类 RTL 和九案例 native 验收。
地址时序优化候选正在进行独立五类 RTL 验证，尚不能沿用基线验收结论。
RouteCast 已完成 CPU 契约、真实 RR 前端及 sketch 开发试验，研究机制与限制见其
`README.md` 和 `RESEARCH_PLAN.md`。DieRoute、FusionPAR 当前仍为独立原型。
各工程的阶段性正确性证据不能替代论文所需的完整机制、强 baseline、实现时序或板上实测。

研究推进顺序为 PersistRoute → TilePlace → RouteCast → DieRoute → FusionPAR；
这是研究顺序，不是构建依赖，也不表示五个程序已串接为端到端流水线。

## 无 Vitis 时的功能验证

```powershell
cd C:\Users\20641\Desktop\FPGA_Acc\projects
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\build_all.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\test_all.ps1
```

## 安装 Vitis 2022.2 后

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_all_hls.ps1
```

各工程 `run_hls.tcl` 目标为 U280 `xcu280-fsvh2892-2L-e`、4 ns，执行 C simulation、synthesis、Verilog co-simulation 和 `.xo` 导出。换板前修改各自 `set_part`。

HLS 导出 RTL 后可用通用 Vivado 检查入口：

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File .\run_vivado_post_synth.ps1 `
  -ProjectName <HLS顶层模块名> -RtlDir <HLS导出的RTL目录>
```

该入口生成 post-synthesis DCP、utilization 和 timing summary；安装 Vivado 前不会产生虚构报告。

## 后四个工程尚未完成的部分

- 各工程尚未覆盖的真实 VPR 9、Titan23/Koios 前后端与架构泛化验证（已完成部分见各工程记录）；
- FPGAIF/RapidWright UltraScale+ PIP、route tree和timing导入；
- 各自论文机制所需的完整 queue/multi-PE/HBM/XRT host；
- Vivado合法性、时序、post-route面积/Fmax/功率；
- 与 VPR/RWRoute/CUFR/Potter/DiffRouter 等强baseline的论文实验。

这些内容依赖数据转换、工具和板卡，后续应从 TilePlace 开始逐工程实现和验证，
不能把 PersistRoute 的完成状态外推到后四篇。
