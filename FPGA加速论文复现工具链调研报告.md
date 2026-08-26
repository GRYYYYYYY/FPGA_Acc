# 近年 FPGA 加速论文复现与 Vivado/Vitis 版本选择调研报告

**调研日期：** 2026-08-12  
**范围：** 以 2021—2025 年公开论文/Artifact 为主，兼顾其仍被广泛使用的 2019.2—2023.1 工具链  
**目标：** 为论文实验对比选择兼容面较广、迁移风险较低的 AMD/Xilinx FPGA 开发环境

## 1. 结论先行

### 1.1 推荐安装方案

| 优先级 | 建议 | 用途 |
|---|---|---|
| 必装 | **Vitis 2022.2（包含 Vivado 2022.2）**，Linux 原生安装 | 作为主力环境。覆盖 Alveo、Zynq/Zynq MPSoC、RTL、Vitis HLS 和 Vitis 加速流程，且位于 2020.2 与 2023.1 两个论文高频版本之间 |
| 建议并装 | **Vitis 2020.2（包含 Vivado 2020.2）** | 精确复现大量 2021—2024 年论文中冻结的 HLS/IP/Block Design，尤其 FINN、稀疏视觉、密码学和早期 Vitis 工程 |
| 按需并装 | **Vitis 2023.1（包含 Vivado 2023.1）** | FlightLLM、HLSFactory 等较新 Artifact；也适合作为新设计和 HLS QoR 对照版本 |
| 暂不作为主环境 | 2024.x、2025.x、2026.1 | 与多数论文原始环境不一致；升级 IP、Vitis IDE/命令流变化会引入额外变量。2026.1 还引入新的分级许可模式 |

**若只能安装一个版本：选 2022.2。** 这是“广泛复现”的折中选择，不代表它能无修改打开所有旧工程。凡论文或仓库明确指定版本，应优先使用原版本。

**若追求严谨的论文数值对比：建议三版本共存：2020.2 + 2022.2 + 2023.1。** 不要把旧工程直接保存为新版本；先复制工程或从 Tcl/源码重新生成。

### 1.2 推荐操作系统与硬件资源

- 主机系统：**Ubuntu 20.04 LTS** 最适合作为 2020.2/2022.2 的共同基线；2023.1 可视官方支持矩阵另设 Ubuntu 22.04 环境。
- 更稳妥的组织方式：每个工具版本使用独立系统镜像、虚拟机或独立 Linux 分区；综合/实现直接在 Linux 主机运行，避免 Windows/WSL 路径和驱动差异。
- 内存：最低 32 GB，建议 **64 GB**；U250/U280/VCU118 等大器件建议 128 GB。
- 磁盘：三套工具、器件库、XRT、平台文件、PetaLinux 和工程缓存建议预留 **500—800 GB SSD**。AMD 对 Vitis 2022.2 给出的最低磁盘空间是 150 GB，内存为 32 GB、推荐 64 GB（[UG1400 2022.2](https://docs.amd.com/r/2022.2-English/ug1400-vitis-embedded/Installation-Requirements)）。

## 2. 为什么不是直接安装最新版

FPGA 论文的可复现性不仅由 C/C++、RTL 源码决定，还由以下一整套版本锁定关系决定：

1. Vivado 内置 IP 每个版本通常只提供该发行版对应的一个版本。旧工程进入新 Vivado 后，IP 可能被锁定或要求升级；若缺少旧版本生成的 output products/DCP，旧 IP 甚至不可用（[AMD：IP 状态说明](https://docs.amd.com/r/2023.2-English/ug896-vivado-ip/Understanding-IP-States-Within-a-Project)）。
2. IP 大版本升级可能改变端口或要求修改 RTL。AMD 建议升级前归档工程、保留生成物，并检查 `report_ip_status` 和 change log（[AMD：Upgrading IP](https://docs.amd.com/r/2024.2-English/ug896-vivado-ip/Upgrading-IP)）。
3. Vitis 工程同时依赖 Vitis、Vivado、XRT、目标平台 `.xpfm`、shell/DSA 和驱动。版本不齐即使 HLS 能综合，也可能无法链接 `.xclbin` 或上板。
4. PetaLinux/Yocto、设备树、sysroot 与 Vivado/Vitis 版本通常也应配套。只升级其中一个组件会增加定位成本。
5. 工具版本会改变 HLS 调度、资源估计、综合优化、布局布线随机性与时序结果。若论文比较 LUT/DSP/BRAM、Fmax、功耗或端到端延迟，换版本本身就是实验变量。

因此，“能打开工程”不等于“复现论文结果”。严格复现应使用作者版本；移植到统一版本则应被标为 **port/reimplementation**，并单独报告版本影响。

## 3. 近年代表性论文与 Artifact 样本

下表优先收录能从论文、Artifact Appendix 或代码仓库确认工具/平台的信息。版本未明确者不据年份猜测。

| 年份 | 工作 | 方向/平台 | 已确认工具信息 | 对安装决策的意义 | 证据强度 |
|---|---|---|---|---|---|
| 2021 | **GraphLily**（ICCAD 2021） | 图线性代数，Alveo U280 | 论文写明 Vitis **2019.2** | 旧 Alveo/Vitis 论文仍可能要求 2019.2；2022.2 只能作为移植环境 | 论文原文（[PDF](https://huyuwei.github.io/files/graphlily-iccad2021.pdf)） |
| 2021 | **AutoSA**（FPGA 2021）及 AutoBridge 流程 | 自动脉动阵列，Alveo U250 | 教程测试环境为 Vivado HLS/Vitis **2019.2** | 自动生成/楼层规划工具常依赖旧报告格式，不宜盲目升级 | 官方项目文档（[AutoBridge 教程](https://autosa.readthedocs.io/en/latest/tutorials/auto_bridge.html)） |
| 2022 | **DP-HLS** | 生物信息二维动态规划，AWS FPGA | 仓库推荐 AWS FPGA Developer AMI，Vitis **2021.2** | 2021.2 是另一兼容点，但通常可先在 2022.2 做 HLS，再按需补装 | 作者仓库（[GitHub](https://github.com/TurakhiaLab/DP-HLS)） |
| 2022 | **FAB**（HPCA 2023，工作形成于 2022） | 全同态加密，Alveo | Vivado **2020.2**，并由 Vitis 生成 `.xclbin` | 密码学加速器大量依赖 2020.2 IP/HLS 行为 | 论文（[PDF](https://bu-icsg.github.io/publications/2023/fhe_accelerator_fpga_hpca2023.pdf)） |
| 2022 | **Auto-ViT-Acc** | Vision Transformer 自动量化/加速 | 论文确认 FPGA 实现，但检索到的公开材料未可靠标出精确工具版本 | 可用于算法/架构比较，复现前必须查仓库 commit 或询问作者，不应自行假定版本 | 论文（[arXiv](https://arxiv.org/abs/2208.05163)） |
| 2023 | **GNNBuilder**（FPL 2023） | GNN HLS 自动生成 | 需要 Vitis HLS、Vivado、Vitis，作者建议 Linux；公开首页未固定版本 | 显示完整工具套件而非单装 Vivado 的必要性 | 作者仓库（[GitHub](https://github.com/sharc-lab/gnn-builder)） |
| 2023 | **DGNN-Booster** | 动态 GNN，ZCU102 | 公开代码与上板测量；当前检索材料未可靠给出精确版本 | 主环境 2022.2适合先做兼容性审查，但严格结果需锁定作者 commit/环境 | 论文（[arXiv](https://arxiv.org/abs/2304.06831)） |
| 2023 | **Rosebud**（ASPLOS 2023） | FPGA 网络中间件 | Artifact 依赖 Vivado 工具链与双 FPGA 测试环境 | 网络/PCIe 论文的主要门槛常是板卡、shell 和驱动，不只是 Vivado | Artifact 附录（[PDF](https://cseweb.ucsd.edu/~schulman/docs/asplos23-rosebud.pdf)） |
| 2024 | **ESDA**（FPGA 2024） | 事件视觉稀疏数据流 | 仓库明确依赖 Vivado **2020.2**，新版本可能需手改 Tcl | 强力支持保留 2020.2 复现环境 | 作者仓库（[GitHub](https://github.com/CASR-HKU/ESDA)） |
| 2024 | **FlightLLM**（FPGA 2024） | LLM 推理，U280/VHK158 | 论文写明使用 Vitis **2023.1** 做 RTL emulation；公开 U280 测试 Artifact | 复现近期 LLM FPGA 工作应准备 2023.1 | 论文与 Artifact（[PDF](https://nicsefc.ee.tsinghua.edu.cn/nics_file/pdf/3fa036e2-0d62-45c4-81e2-20d9b7189504.pdf)、[GitHub](https://github.com/FlightLLM/flightllm_test_demo)） |
| 2024 | **HLSFactory**（MLCAD 2024） | HLS 数据集、QoR 预测/设计空间 | Artifact 明确使用 Vitis HLS **2023.1**、Vivado **2023.1**，并比较 2021.1 与 2023.1 | 适合用来量化“工具版本对 QoR 的影响”；支持并装 2023.1 | 论文 Artifact（[PDF](https://lca.ece.utexas.edu/pubs/HLSFactory_MLCAD_2024.pdf)） |
| 2024 | **vFPIO**（USENIX ATC 2024） | FPGA I/O 虚拟化，双 U280 | Artifact 明确 Vivado **2022.1** 编译/烧写 bitstream | 2022.x 是系统型 FPGA 论文的重要版本簇 | Artifact（[PDF](https://www.usenix.net/system/files/atc24-chen-jiyang.pdf)） |
| 2024 | **ACAI**（USENIX Security 2024） | 可信加速器/系统，VCU118 | Artifact 合集中要求 Vivado **2022.2** 构建 bitstream | 直接支持把 2022.2 作为主环境 | Artifact 合集（[PDF](https://www.usenix.org/sites/default/files/sec24_full_artifact_proceedings.pdf)） |
| 2025 | **Nyx**（ISCA 2025） | 共享 FPGA 上的数据流虚拟化，U250 | Artifact 要求 Vivado **2022.2** 加载初始 bitstream，并提供源码/bitstream | 新论文仍使用 2022.2，说明其作为复现基线不过时 | ACM Artifact 信息（[页面](https://doi.org/10.1145/3695053.3731094)） |

补充样本：开源 TRIDENT Poseidon 哈希加速器明确使用 Vivado **2021.2** 和 C1100；其工程包含 Block Design、XDMA 与自定义 IP，能代表版本敏感型 PCIe 加速器（[GitHub](https://github.com/datenlord/TRIDENT)）。FastHomNAND 同时给出 Vitis HLS/Vitis/Vivado **2020.2** 工程（[GitHub](https://github.com/DHLSan/FastHomNAND)）。这些不一定都是本报告时间窗内的顶会 Artifact，但对“实际可复现仓库的版本分布”有参考价值。

## 4. 版本选择的量化判断

根据上述可确认版本的样本，可以观察到：

- **2019.2—2021.2：** 早期 Vitis、AutoSA/AutoBridge、GraphLily、部分 FINN 和 AWS FPGA 工程集中于此。它们常含已停止维护的脚本、平台名或报告解析器。
- **2020.2：** 是近年开源 RTL/HLS Artifact 中非常常见的“冻结版”，特别值得保留。
- **2022.1/2022.2：** 系统、I/O、安全、Alveo shell 类论文的高频区间；2022.2 同时支持较新的 Ubuntu 20.04/22.04 环境，是最平衡的主版本。
- **2023.1：** 近期 LLM/HLS 数据集工作开始采用；对于较新的 HLS C++、MLIR/HLS 数据生成和 U280 设计有价值。
- **2023.2 以后：** 可用于新项目，但对论文复现的边际覆盖提升有限，且 IDE/命令流、PetaLinux/Yocto 和 IP 继续变化。

### 4.1 决策矩阵

评分为 1（弱）到 5（强），是针对“论文复现平台”而不是普通产品开发。

| 指标 | 2020.2 | 2022.2 | 2023.1 | 2024.x/2025.x | 2026.1 |
|---|---:|---:|---:|---:|---:|
| 对 2021—2024 开源 Artifact 的原生匹配 | 5 | 5 | 4 | 2 | 1 |
| 对较新器件/库的支持 | 2 | 4 | 4 | 5 | 5 |
| 旧 IP/Block Design 迁移风险（分高表示风险低） | 5 | 4 | 3 | 2 | 1 |
| Linux 论文环境适配 | 4 | 5 | 5 | 4 | 受新许可影响 |
| 作为单一主版本的平衡性 | 3 | **5** | 4 | 3 | 2 |
| 适合严格复现 | 对指定 2020.2 的论文为 5 | 对指定 2022.x 的论文为 5 | 对指定 2023.1 的论文为 5 | 仅对同版本论文高 | 目前样本少 |

## 5. Vivado 还是 Vitis：应该安装什么组件

### 5.1 只安装 Vivado 的情况

满足以下全部或大部分条件时，只需 Vivado：

- 论文提供 Verilog/SystemVerilog/VHDL 或已导出的 HLS RTL/IP；
- 目标是 RTL 仿真、综合、实现、时序和资源对比；
- 不需要从 C/C++ 重新跑 HLS；
- 不需要生成 Alveo `.xclbin`、XRT host 程序或嵌入式软件。

### 5.2 应安装 Vitis 的情况

论文复现通常建议直接装完整 Vitis，因为 Vitis 软件平台本身包含实现 kernel/平台所需的 Vivado（[AMD Vitis 2022.2 安装要求](https://docs.amd.com/r/2022.2-English/ug1400-vitis-embedded/Installation-Requirements)）。以下任一情况都需要或强烈建议 Vitis：

- C/C++ 高层综合（Vitis HLS）；
- Alveo U200/U250/U280/U50/U55C 的 host + kernel + XRT 流程；
- Zynq/MPSoC 的 bare-metal/Linux 应用开发；
- 需要构建 `.xo`、链接 `.xclbin` 或使用 Vitis Libraries；
- 论文仓库的 Makefile/Tcl 直接调用 `v++`、`vitis_hls`、`platforminfo` 等命令。

### 5.3 可能还需要的配套组件

- **XRT 和对应 deployment/runtime 包：** Alveo 上板必需，版本应与 platform/shell 对齐。
- **板卡 platform `.xpfm`：** 同型号板卡也可能有多个 shell/platform 版本。
- **PetaLinux：** 自定义 Zynq/MPSoC Linux 镜像、设备树和驱动时需要；版本尽量与 Vivado/Vitis 同年同小版本。
- **Vitis AI：** 只有使用 DPU/VART/量化编译器的论文才需要；它有自己的版本矩阵，不能用“装了 Vitis”替代。
- **Model Composer、MATLAB/Simulink：** 仅在论文明确使用时安装。
- **器件支持包：** 安装时至少选择实际板卡系列；U280/VCU118/C1100 等高端器件还要先确认许可证。

## 6. 建议的实验环境布局

推荐在 Linux 文件系统中保持严格隔离：

```text
/opt/Xilinx/2020.2/        # Vitis、Vivado、Vitis_HLS
/opt/Xilinx/2022.2/        # 主环境
/opt/Xilinx/2023.1/        # 新 HLS/LLM Artifact
/opt/xilinx/platforms/<release>/
/opt/xilinx/xrt/<release>/
/data/fpga-artifacts/<paper>/<commit>/
/data/fpga-results/<paper>/<tool-version>/<run-id>/
```

每次只 source 一套环境，建议使用独立启动脚本或 Environment Modules，不要在全局 shell 配置中同时加入多个版本：

```bash
source /opt/Xilinx/Vitis/2022.2/settings64.sh
vivado -version
vitis_hls -version
v++ --version
```

对 Alveo 还应记录：

```bash
xbutil examine
xbmgmt examine
platforminfo -l
```

实际安装路径会因 Unified Installer 的目录结构而异，以上仅作布局示例。

## 7. 面向论文对比的复现流程

### 阶段 A：复现资格筛选

为每篇候选论文建立清单：

1. 论文版本/DOI、代码仓库 URL、commit hash、Artifact/Zenodo DOI；
2. 原始 Vivado/Vitis/Vitis HLS/PetaLinux/XRT 版本；
3. 板卡、器件完整 part number、shell/platform 版本；
4. 是否提供 bitstream、DCP、XCI/XCIX、Tcl、HLS C++、host code、数据集和模型权重；
5. 许可证、闭源 IP、板卡和数据集是否可获得；
6. 论文指标是否能在相同输入、精度、batch size、频率和功率口径下比较。

若缺少精确版本，不要立即全量实现。先检查 `README`、Artifact Appendix、Dockerfile、CI、Makefile、Tcl 中的路径，以及 Vivado 工程文件头；仍无法确定时再联系作者。

### 阶段 B：三级复现

| 级别 | 目标 | 所需条件 | 可比较结果 |
|---|---|---|---|
| L1 软件/功能复现 | 模型、算法、C/RTL 仿真正确 | 源码、数据/权重 | 准确率、功能正确性、操作数 |
| L2 工具复现 | HLS/综合/实现成功 | 原工具版本、器件、IP/约束 | LUT/FF/DSP/BRAM/URAM、Fmax、估算延迟/功耗 |
| L3 上板复现 | 端到端运行 | 同板卡、shell/XRT/驱动、host 环境 | 吞吐、端到端延迟、板上功耗、能效 |

做论文对比时必须标注达到哪个等级。只做 C simulation 或 HLS estimate，不能声称复现了板上吞吐和能效。

### 阶段 C：版本敏感性实验

对于计划作为论文 baseline 的设计，建议固定源码和约束，至少比较：

- 作者原始版本；
- 统一基线 2022.2；
- 若研究 HLS/LLM，再加 2023.1。

每版至少进行 3 次独立实现（清空实现 run，不复用旧 DCP），报告中给出中位数和范围。布局布线随机性、工具默认 directive 变化和时钟约束都可能影响 Fmax。

## 8. 结果记录模板

建议为每次实验保存以下元数据：

```yaml
paper: FlightLLM
repo_url: https://github.com/FlightLLM/flightllm_test_demo
commit: <full SHA>
tool:
  vivado: 2023.1
  vitis_hls: 2023.1
  vitis: 2023.1
  xrt: <exact version>
platform:
  board: Alveo U280
  part: <exact part>
  xpfm: <exact platform name/version>
host:
  os: <distribution and point release>
  kernel: <version>
  cpu: <model>
experiment:
  clock_mhz: <target/achieved>
  precision: <e.g. INT4/INT8>
  batch_size: 1
  dataset_or_model: <name and checksum>
result:
  lut: <used>
  ff: <used>
  bram: <used>
  uram: <used>
  dsp: <used>
  throughput: <value and unit>
  latency: <value and scope>
  power_w: <measurement method>
```

同时归档 `vivado.log`、`vivado.jou`、HLS report、utilization/timing/power report、bitstream/xclbin checksum、运行命令和原始测量数据。

## 9. 常见复现失败及处理顺序

1. **IP locked / VLNV 不存在：** 首选切回作者版本；其次检查作者是否提交 output products/DCP；最后才复制工程并执行 IP upgrade。不要覆盖原工程。
2. **Tcl 属性或命令失效：** 检查脚本生成的 Vivado 版本；为不同版本维护小型 patch，而不是直接重写整个工程。
3. **找不到 platform：** 核对 `.xpfm` 的完整名字和 release；平台不是仅凭“U280”型号就能互换。
4. **XRT/driver 与 xclbin 不兼容：** 对齐 XRT、shell、platform 和 Vitis；先用 `xbutil validate` 验证板卡基础环境。
5. **HLS C++ 编译失败：** 检查 HLS 头文件 API、任意精度类型、旧 pragma、C++ 标准和 host GCC；不要把 host 编译问题误判为硬件设计错误。
6. **综合能过但时序/资源不一致：** 核对 part、时钟、不确定性、strategy/directive、IP 版本、约束是否读取、随机种子和工程增量缓存。
7. **板上性能不一致：** 区分 kernel latency 与端到端 latency；核对 PCIe/HBM 传输、数据预处理、batch、模型精度、频率和功率测量口径。

## 10. 许可与下载注意事项（截至 2026-08-12）

AMD 从 Vivado **2026.1** 开始采用新的分级许可。官方页面说明 BASIC 免费但需要年度许可；高端 UltraScale/UltraScale+、Versal、完整仿真/调试和高级功能可能需要更高等级。Vitis 后端调用 Vivado 也需要有效 Vivado tier license（[AMD Vivado Licensing Options](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/vivado/vivado-licensing-options.html)）。

这进一步支持本报告不把 2026.1 作为当前论文复现主环境。旧版下载可从 AMD/Xilinx 的 [Vivado 下载归档](https://www.xilinx.com/support/download.html/content/xilinx/en/downloadNav/vivado-design-tools/archive.html) 获取，但高端器件/IP 是否需要许可证必须按具体板卡和学校授权确认。高校研究团队可评估 AMD University Program。

## 11. 最终采购/安装建议

### 情形 A：已有 Zynq-7000、ZCU102、KV260 等嵌入式板卡

- 主装 Vitis/Vivado 2022.2；
- 为 2020.2 Artifact 保留独立 Ubuntu 20.04 环境；
- 需要 Linux 镜像重建时，配套安装同版本 PetaLinux；
- 若只比较 HLS/资源，无需立刻购买高端 Alveo。

### 情形 B：已有或计划购买 Alveo U250/U280

- 首先按目标论文反查原始 platform/shell 和 XRT，而不是先决定最新版工具；
- 主装 2022.2，并装 2023.1；对 GraphLily/AutoSA 等旧 baseline 准备 2019.2 的可归档环境或作者预编译 bitstream；
- 购买前确认 PCIe 插槽、供电、散热、服务器 BIOS/IOMMU、OS 和许可证；
- 同一板卡型号不能保证不同论文的 xclbin 可直接互用。

### 情形 C：尚无板卡，以发论文对比为目标

- 先用 2022.2 完成 RTL/HLS 仿真、综合和统一器件下的资源/时序比较；
- 从带 Artifact、代码完整、无需闭源 IP 的论文中筛选 2—4 个 baseline；
- 再根据共同板卡决定采购。若研究图/LLM/大模型内存系统，U280 的论文生态更丰富但成本和许可门槛高；若研究边缘 CNN/GNN/事件视觉，ZCU102/Kria 更易开展完整上板实验；
- 最终论文中同时给出“作者原平台报告值”和“本工作统一平台实测值”，不要把二者混为一组公平对比。

## 12. 可直接执行的行动清单

1. 安装 Ubuntu 20.04 LTS 原生环境，准备至少 500 GB 可用 SSD 和 64 GB RAM。
2. 下载并安装 **Vitis 2022.2**，只勾选实际需要的器件族以节约空间。
3. 建立一个最小验证工程，运行 Vitis HLS C simulation、C synthesis、Vivado implementation。
4. 根据第一批 baseline 是否明确要求，安装 **2020.2**；若包含 FlightLLM/HLSFactory，再安装 **2023.1**。
5. 建立上述 YAML 元数据与原始报告归档规范。
6. 对每个 baseline 先完成 L1/L2，再投入时间解决 L3 的板卡和驱动问题。
7. 在正式对比前做一次工具版本敏感性实验，确认 Vivado/Vitis 版本变化是否显著改变资源、Fmax 或延迟。

---

### 调研限制

- “近几年 FPGA 加速论文”范围很大，本报告采用了代表性抽样，而非穷尽所有会议论文。
- 只把论文、Artifact Appendix、作者/项目仓库明确写出的版本视作可靠版本证据；未明确者已标注，不以发表年份推断。
- Intel FPGA/Quartus、Microchip Libero、开源 Yosys 流程不在本次 Vivado/Vitis 安装决策范围内。
- 板卡库存、旧版下载权限、操作系统支持与许可证会变化；实际安装前应再次核对 AMD 官方下载页和目标仓库的固定 commit。
