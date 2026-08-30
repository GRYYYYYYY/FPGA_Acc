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
论文材料闭环，但仍缺物理板 runtime/能耗。其余四个工程仍处于 HLS 骨架阶段；
下一项 TilePlace 必须先完成真实 VPR placement 前端、CPU golden 和写回合法性，
不能把当前小型 testbench 数字作为投稿结果。

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

- TilePlace/RouteCast/DieRoute/FusionPAR 的真实 VPR 9、Titan23/Koios 前后端；
- FPGAIF/RapidWright UltraScale+ PIP、route tree和timing导入；
- 各自论文机制所需的完整 queue/multi-PE/HBM/XRT host；
- Vivado合法性、时序、post-route面积/Fmax/功率；
- 与 VPR/RWRoute/CUFR/Potter/DiffRouter 等强baseline的论文实验。

这些内容依赖数据转换、工具和板卡，后续应从 TilePlace 开始逐工程实现和验证，
不能把 PersistRoute 的完成状态外推到后四篇。
