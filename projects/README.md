# 五篇论文的五个独立工程

| 工程 | 论文 | 当前可综合顶层 | 独立科学边界 |
|---|---|---|---|
| `tileplace` | TilePlace | `tileplace_kernel` | 时序异构页分配与确定合法位置 |
| `routecast` | RouteCast | `routecast_kernel` | FPGA RR语义增量routing sketch |
| `persistroute` | PersistRoute | `search_kernel`, `commit_kernel` | 路由搜索、版本事务与确定提交 |
| `dieroute` | DieRoute | `dieroute_kernel` | SLL预留、shadow版本和die队列映射 |
| `fusionpar` | FusionPAR | `fusionpar_kernel` | 原子move-route-repair共享状态协议 |

五个目录不引用彼此头文件或源码，每个都能独立复制、构建和归档。当前 HLS code/testbench/Tcl 已写好，但真实论文实验仍需接 VPR/FPGAIF/RapidWright 数据、强软件 baseline 和板卡运行；不能把当前小型 testbench 数字作为投稿结果。

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

## 尚未伪装成“完成”的部分

- 真实 VPR 9 RR graph、Titan23/Koios；
- FPGAIF/RapidWright UltraScale+ PIP、route tree和timing导入；
- 完整 bucket/MultiQueue、multi-PE、HBM/XRT host；
- Vivado合法性、时序、post-route面积/Fmax/功率；
- 与 VPR/RWRoute/CUFR/Potter/DiffRouter 等强baseline的论文实验。

这些内容依赖数据转换、工具安装和板卡，后续应逐工程继续实现和验证，不能仅凭当前 HLS 骨架宣称五篇论文的全部系统已经完成。
