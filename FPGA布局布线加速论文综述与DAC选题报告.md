# FPGA 布局布线加速论文综述与五篇 DAC 选题报告

**版本：** v1.0（2026-08-13）  
**研究总目标：** 形成 2 篇 FPGA 布局加速、2 篇 FPGA 布线加速、1 篇 FPGA 布局布线联合加速的独立投稿工作。  
**目标会议：** DAC 为首选；按贡献侧重可转投 ICCAD、FPGA、ISPD、FCCM、FPL、DATE、ASP-DAC。  
**工具链基线：** 主力原型使用 Vitis/Vivado 2022.2；严格复现服从各论文/仓库固定版本；FPGA 2024 Routing Contest 的 Vivado 校验环境独立维护。

> 本报告是研究执行纲领，不是录用承诺。“完成一篇”指冻结代码、可复现实验、论文正文和投稿包均具备；五篇必须各自包含新的科学问题、算法机制、配套硬件机制和不可由前作直接推出的主要实验结果。

## 1. 结论先行

最优执行顺序是 **PersistRoute → TilePlace → RouteCast → DieRoute → FusionPAR**。原因不是优先做最容易的论文，而是 PersistRoute 能最早建立商业 FPGA 图、合法性、时序、指标和硬件数据面，后四篇均可复用其基础设施，同时又不复用其核心 claim。

五篇的可辩护核心分别是：

1. **TilePlace：** 时序驱动的异构 FPGA 页分治与确定性硬件合法化；
2. **RouteCast：** 基于真实 FPGA RR 资源语义的低精度 routing sketch 反馈，而非 ASIC 风格拥塞图；
3. **PersistRoute：** 单 die 商业 FPGA 上跨 RRR 迭代常驻状态、两级并行和确定性事务提交；
4. **DieRoute：** 多 die/SLR 的 SLL 容量预留、HBM 分区和边界 shadow state；
5. **FusionPAR：** placement move、routing transaction 与局部 repair 的共享状态交错协议。

“更多 PE、换成 HBM、批量独立 net、普通 maze-routing 流水线、只报告 kernel speedup、把前四篇简单连接起来”均不能成为主贡献。

## 2. 不可越界的研究定义

### 2.1 研究对象

这里的“FPGA 加速 FPGA 布局布线”有两个 FPGA：

- **被求解对象**是可重构 FPGA 的 packing、placement 和 routing；
- **执行平台**是作为 CAD 加速器的 FPGA 板卡。

被求解对象必须显式覆盖 FPGA 的离散资源和约束：CLB/LUT/FF、BRAM、DSP、IO、cascade、clock region、预制 segment、PIP/switch box、pin equivalence、局部互连、长线以及多 die 时的 SLL。

### 2.2 ASIC 文献只允许迁移什么

| 可迁移的加速思想 | 可落地形式 | 不可迁移的问题模型 |
|---|---|---|
| 数据流重构与算子融合 | 把增量代价、队列、提交和统计组织成流式模块 | ASIC 标准单元行、宏/单元重叠目标 |
| 分层存储、压缩、缓存、预取 | FPGA tile 模板化 RR 图、热点窗口、HBM channel 映射 | 金属层/via 图、design-rule checking |
| 动态调度与负载均衡 | 按 bbox、criticality、历史冲突率调度 connection | ASIC net 的独立小图假设 |
| 冲突检测和投机执行 | RR resource version、read/write set、确定性 commit | 把 ASIC detailed router 的冲突语义直接照搬 |
| 持久状态与增量更新 | occupancy、present/history cost、route tree 跨 RRR 常驻 | 仅以“状态常驻”本身声称新颖 |
| 软硬件划分和端到端核算 | 主机解析/异常回退，FPGA 正常 RRR；报告 PCIe 和预处理 | 只比较 kernel、忽略合法化和输出 |

Ripple 和 SimPL 的本地论文分别用于理解“反馈闭环如何嵌入 placement”和“简洁算法如何暴露线程/SIMD并行”，不用于定义 FPGA placement。DREAMPlace、DG-RePlAce、CUGR、GAMER、FastGR、ASP-DAC 2022 maze kernel、RouterAcc 同理，只进入加速机制层。

### 2.3 FPGA 算法来源链

若使用 directed search、maze expansion、negotiated congestion 或 timing-driven cost，算法来源必须写为：

`PathFinder/VPR → connection-aware FPGA routing → RWRoute/RapidWright commercial FPGA semantics → 本工作的硬件化与新并行协议`

不得写成：

`ASIC A* accelerator → 换一个 FPGA 图 → FPGA router`

两者的根本差异是：FPGA 在预制、方向和长度离散的互连资源上选择 PIP/segment，容量、pin equivalence、route tree reuse 和时序类均由器件架构决定；ASIC 则涉及连续几何到多金属层、via 和设计规则的另一类约束。

## 3. 2018—2026 文献图谱与可用结论

机器可筛选的 31 项记录见 [论文矩阵.csv](./论文矩阵.csv)。矩阵把“FPGA 算法/实现”和“ASIC 加速机制参考”拆成不同类别，并提供“禁止误用”字段。

### 3.1 FPGA placement：从异构解析布局到硬件页布局

- **RippleFPGA（TCAD 2018）**将 packing 与 placement 同时处理，包含 FPGA 路由架构感知优化和专用合法性检查；本地论文报告 routed wirelength 改善 5.1%、速度提升 5.5×。它说明 RouteCast 必须与最终精确路由结果闭环，而不仅是 HPWL。
- **AMF-Placer（ICCAD 2021）/AMF-Placer 2.0**建立了大规模混合尺寸、异构和时序驱动 FPGA 解析布局基线。TilePlace 不能只说“支持 BRAM/DSP”，必须证明异构页分解和硬件合法化相对这些强软件方法的独立价值。
- **elfPlace（ICCAD 2019/TCAD 2022）、DREAMPlaceFPGA（ASP-DAC 2022）、DREAMPlaceFPGA-PL（ISPD 2023）与 DREAMPlaceFPGA-MP（2023）**分别提供确定性 GPU 异构全局布局、GPU 解析布局、GPU packing/legalization，以及 cascade shape 和 region constraint 的宏布局强基线。GPU 是必须做的等质量平台对照，而不是可选背景。
- **OpenPARF**适合作为统一数据库/算子框架，但不能因为名称含 placement and routing 就推断它具备 UltraScale+ 精确商业路由能力。
- **RapidLayout（TRETS 2022）**针对规则脉动阵列的 hard-block placement、跨 SLR 和 route reuse；其适用场景较窄，不能外推成通用完整布局基线，但 TilePlace/DieRoute 必须讨论它。
- **Hardware Accelerated FPGA Divide-and-Conquer Page Placement in Milliseconds（FPGA 2026）**已经占据“硬件分治页布局、毫秒级”位置。公开索引确认其使用位置级 systolic 结构；任何关于线长、时序差距、异构支持和端到端范围的精确判断均须取得全文后复核。TilePlace 只有同时给出“时序/异构问题的新算法 + 新硬件机制 + routed QoR”才足够独立。[DBLP 记录](https://dblp.uni-trier.de/rec/conf/fpga/Thomas0D26)；[DOI](https://doi.org/10.1145/3748173.3779190)。

### 3.2 FPGA routing：并行性、商业语义与最新威胁

- **确定性并行 FPGA routing（FPL 2018）**已经研究确定/非确定并行执行权衡，因此 PersistRoute 不能声称“第一个确定性并行 router”；新意必须落在硬件事务提交、版本状态和跨 RRR 常驻。
- **connection-aware parallelization（TRETS 2020）**已经把 connection 作为并行粒度；**MultiQueue-Based FPGA Routing（FPT 2024）**又探索了单 connection 内 relaxed priority queue。因此两级并行是必要组合，但组合本身仍需事务协议和硬件证据才能成为新贡献。
- **RWRoute（TRETS 2021）**是 UltraScale+ 时序驱动开放基线。其本地论文给出与 Vivado 平均约 2% 的时序模型精度，并覆盖长线、pin equivalence 和商业器件合法路径。它必须作为 PersistRoute 的语义源和验证基线，而不是只拿 Vivado 黑盒时间比较。
- **CUFR（GLSVLSI 2024）**用递归三叉分区和混合拥塞系数更新提高多 net 并行；本地论文在 FPGA24 设计上报告约 2× RWRoute/Vivado，并改善关键路径线长。其公开 Java 类可从 [RapidWright 文档](https://www.rapidwright.io/javadoc/com/xilinx/rapidwright/rwroute/CUFR.html)核验。
- **Potter（ICCAD 2024）**已提出商业 UltraScale+ 的 overlap-tolerant 并行 router。它是 PersistRoute 最接近的先验：不能再以“允许重叠任务”为标题级创新，而要证明 versioned transaction、固定提交序、硬件 rollback/replay 和持久状态解决了 CPU 方法没有解决的体系结构问题。
- **AceRoute（ICCAD 2024）**已经通过自适应瓶颈识别和可插拔 connection 内双向探索组合细粗粒度并行。因此 PersistRoute 还不能把“单 connection 内并行”或“双向搜索”作为首次贡献，必须比较其自适应计算效率。
- **DiffRouter（FCCM 2026）**把 UltraScale routing 连续化并用 GPU 梯度优化，再投影回合法解。这是新的 GPU 强基线，也说明论文必须比较“离散事务式 RRR”与“连续大规模并行”的速度、内存和 QoR边界。[DOI](https://doi.org/10.1109/FCCM68464.2026.00029)。

### 3.3 商业器件公开验证入口

FPGA 2024 Runtime-First Routing Contest 提供预放置、部分预布线的 FPGA Interchange 设计、RWRoute 起点与 Vivado 合法性/关键路径线长校验，是 PersistRoute、RouteCast 和 FusionPAR 的主要商业入口。官方说明要求输出完整 FPGAIF 路由解并用 `report_route_status` 检查，评分同时考虑 runtime 与 critical-path wirelength：[getting started](https://xilinx.github.io/fpga24_routing_contest/start.html)、[details](https://xilinx.github.io/fpga24_routing_contest/details.html)、[results](https://xilinx.github.io/fpga24_routing_contest/results.html)。

这套竞赛不能替代完整 benchmark 设计：

- 其输入已经 placement，适合路由，不直接支持 TilePlace 的布局评价；
- 主排名口径不能覆盖总 wirelength、CPD/WNS/TNS、能效和跨随机种子稳定性；
- Vivado 校验依赖许可证和固定版本，必须保留独立环境镜像；
- 竞赛数据可作测试集，但参数调节需另用训练/验证设计，防止面向公开排行过拟合。

### 3.4 ASIC 加速工作给出的真正启发

| 工作 | 可学习 | 对本路线的约束 |
|---|---|---|
| DREAMPlace（DAC 2019） | 把传统优化重写为规则张量算子、融合 kernel、分析 Amdahl 瓶颈 | TilePlace/RouteCast 要重构 FPGA 专用状态，不移植 ASIC placement 目标 |
| DG-RePlAce | 数据流感知聚类与硬件友好局部性 | 只借鉴 cluster/dataflow 组织 |
| CUGR/GAMER/FastGR | 概率需求、细粒度队列、异构任务图和长尾调度 | 不使用金属层/via/ASIC maze 作为 FPGA 算法来源 |
| ASP-DAC 2022 FPGA maze kernel | 独立小图批处理、流水 PE、统计工作集大小 | PersistRoute 必须覆盖大图、重叠任务、所有 RRR 和全 wall-clock |
| RouterAcc（DATE 2026） | 存储层次、流程协同、持久数据面 | “使用 HBM/持久状态”已不是充分新意；必须与 FPGA 特有 RR 状态和协议绑定 |

## 4. 五篇论文的研究合同

### 4.1 论文一：TilePlace

**暂定题目：** *TilePlace: Hardware-Accelerated Timing-Driven Placement for Heterogeneous FPGAs*

**研究假设：** 对 page partition、assignment 和 stitching 使用 connection criticality 与 FPGA delay class，并在硬件中增量维护 cut-net delay/资源配额，可以在不显著恶化 routed CPD 的前提下取得端到端加速。

**必须实现的算法机制：**

1. 页面状态同时记录 CLB、BRAM、DSP、cascade、clock-region 容量；
2. 分割目标为 `wire_cost + λt·timing_cut + λr·resource_overflow + λb·boundary_cost`；
3. 只更新移动影响的 cut nets、关键度和页面边界，不做全量重算；
4. stitching 后采用资源类型分离、固定 tie-break 的合法化，处理形状与区域约束；
5. 最终用 VPR/PersistRoute/RWRoute 完成精确路由并测 CPD，不能用估计时序替代 routed QoR。

**硬件机制：** page-local systolic/streaming score engine、异构配额 bank、增量 net cache、确定性 prefix/arbiter 合法化。

**主要拒绝检验：** 如果去掉 timing-aware partition 后 routed CPD 差异不显著，或相对 FPGA 2026 页布局只有“增加资源类型”而无算法差异，则停止以 DAC 主线投稿，转为架构/应用型 FPGA 论文或并入 FusionPAR。

**验收：** 强 CPU placement 基线端到端目标 ≥5×；平均 routed CPD 差距目标 ≤2%、最低门槛 ≤5%；100% 合法；至少三种异构比例和两个架构家族。

### 4.2 论文二：RouteCast

**暂定题目：** *RouteCast: FPGA-Resident Routing-Sketch Feedback for Routability-Driven FPGA Placement*

**研究假设：** 具有 segment、方向、switch box、pin equivalence、局部互连和长线语义的稀疏 routing sketch，比 HPWL/bin density 或 ASIC 风格 grid congestion 更能预测最终 FPGA 路由热点；增量硬件更新使高频反馈不拖慢 placement。

**sketch 的边界：** 它不输出精确 route，不声称 detailed-router speedup。每条受影响 connection 仅传播受限 hop/候选模板，生成每类 RR 资源的 demand、saturation 和 detour proxy。

**核心指标：**

- sketch hotspot 与最终精确 `overused RR / RRR iteration / detour` 的 Spearman 相关系数；
- top-k hotspot precision/recall；
- 反馈延迟占布局 wall-clock 比例；
- 最终 route failure、RRR 迭代、wirelength 和 CPD；
- 与 HPWL、RUDY/栅格估计、低频精确 route feedback 的等时间预算比较。

**主要拒绝检验：** 若只在训练设计相关、在隔离测试家族上失效；或高频 sketch 使布局总时间增加而最终 RRR/失败率无显著改善，则不能声称闭环价值。

**验收：** 反馈阶段相对 CPU ≥5×；最终 route failure 和 RRR 迭代显著降低；总布局时间无显著增加；必须单列增量范围与全量 sketch 对照。

### 4.3 论文三：PersistRoute（首篇实施）

**暂定题目：** *PersistRoute: Persistent-State Speculative Routing Acceleration for Commercial FPGAs*

**研究假设：** 在 FPGA/HBM 中跨 RRR 常驻完整 RR 状态，通过 connection 级 + connection 内两级并行和版本化事务提交，可把 CPU 并行 router 的随机访存与同步瓶颈转为可流水、可确定的硬件执行，同时保持 UltraScale+ 时序/QoR。

**算法合同：**

1. 输入 task = `(connection, source, sink, bbox, criticality, old_tree, epoch)`；
2. task scheduler 按空间 footprint、历史冲突率、criticality 形成允许重叠的 batch；
3. PE 内采用 FPGA 路由文献支持的 bucket/multi-queue directed expansion；
4. search 只写本地 candidate path 和 `read_version/write_set`；
5. commit 按 `(epoch, priority, connection_id)` 固定序检查所有 resource version；
6. 成功则原子更新 owner/occupancy/cost/version/route tree；失败则 rollback 或进入 replay queue；
7. FPGA 内执行正常的 congestion update 与终止判断；主机仅做定期 timing snapshot、异常 fallback 和文件导出。

**新意必须是联立的：** Potter 已有 overlap tolerance，connection-aware 和 MultiQueue 已有两级并行的两个组成部分，RouterAcc 已有持久/层次存储。PersistRoute 的 claim 因而必须是“面向商业 FPGA 语义的版本化确定事务 + 跨迭代硬件状态体系 + 端到端实证”，不能拆开声称各自首次。

**验收：** 对强多核开源基线端到端 ≥3×、目标 5×；平均 wirelength/CPD 退化 ≤2%；100% 合法且重复结果 bitwise/route-set 一致；分别报告预处理、PCIe、search、commit、replay、timing update、导出。

### 4.4 论文四：DieRoute

**暂定题目：** *DieRoute: HBM-Partitioned Hierarchical Routing Acceleration for Multi-Die FPGAs*

**研究假设：** 把 RR graph/state/PE cluster 与 die/SLR 及 HBM channel 同构映射，并在 die 内路由前完成 SLL 分配/容量预留，可避免随机跨 channel 访问和后期不可恢复的边界拥塞。

**独立算法机制：**

- 建立 `(die, boundary, SLL class)` 容量图，先为跨 die connection 分配 corridor 与预算；
- critical connection 的 SLL 代价显式包含跨 die delay 和稀缺性；
- 每个 die 保存局部 authoritative state，边界只同步 shadow summary/version；
- 根据 SLL criticality、拥塞和队列长度迁移 task，而非任意搬移 RR 状态；
- 参数化 mesh/stack/线性 SLR 拓扑。

**与 PersistRoute 的边界：** PersistRoute 固定单 die、声明通用 PE/事务；DieRoute 只声明跨 die 分层算法、shadow coherence 和 HBM 映射。无 HBM 分区的 PersistRoute 是最重要消融。

**验收：** route failure 不增加；SLL 使用、跨 die CPD、wirelength 不劣于基线；端到端 ≥3×；展示 die 数、SLL 密度、HBM channel、PE 数的缩放曲线。

### 4.5 论文五：FusionPAR

**暂定题目：** *FusionPAR: Shared-State Interleaved Placement and Routing Acceleration for FPGAs*

**研究假设：** placement 与 routing 共用 architecture/timing/congestion 状态，并把 move、增量 route 与 placement repair 组成事务闭环，可消除顺序 P&R 的重复构图/传输/全局返工；收益不是单纯相加前四篇 speedup。

**新的联合机制：**

1. placement move 产生精确 affected-connection set；
2. 对该集合执行 speculative incremental route；
3. 路由成功则原子提交 placement+route；冲突/失败则产生局部 repair task；
4. convergence controller 依据 overflow、timing slack、repair收益和事务失败率，在 placement、sketch、exact route、repair 间切换；
5. architecture graph、timing snapshot、congestion state 只初始化/传输一次。

**主要拒绝检验：** 若收益可由 `最佳placer + PersistRoute` 顺序组合完全解释，或局部 repair 只是全局 placement 的缩小版，就没有独立论文贡献。

**验收：** 对最佳顺序开源 P&R 端到端目标 ≥5×；平均 CPD/wirelength 退化 ≤2%；普通、拥塞、高扇出、异构设计均合法；分别消融共享状态、增量更新、事务 move-route 和控制器。

## 5. 公共基础设施与独立分支

### 5.1 建议代码组织

```text
fpga-acc-par/
  schemas/                 # 版本化二进制接口，所有论文共享
  converters/
    vpr9/                  # .net/.place/rr_graph/timing 导入导出
    fpgaif/                # FPGA Interchange
    rapidwright/           # Java exporter/validator
  runtime/                 # C++ host、XRT、计时、fallback
  reference/               # 确定性软件 golden model
  hw_common/               # DMA、HBM crossbar、计数器，不作为后续新贡献
  tileplace/
  routecast/
  persistroute/
  dieroute/
  fusionpar/
  experiments/
    manifests/ splits/ scripts/ raw/ processed/ figures/
  third_party/             # 固定commit与补丁清单，不直接混改
```

公共模块在第一篇发表后均作为 baseline/复用组件；每篇保留独立算法开关、bitstream、运行入口和冻结 tag。

### 5.2 软件和数据入口

| 层 | 选择 | 责任 |
|---|---|---|
| 学术架构 | VPR 9 | Titan23、Koios、学术架构、合法性/QoR参考 |
| 商业器件 | FPGAIF + RapidWright/RWRoute | UltraScale+ device graph、设计导入、路由与时序验证 |
| 工业参考 | Vivado | 合法性、时序、QoR和完整商业流参考；不依赖内部不可见阶段作为唯一基线 |
| 加速器 | Vitis HLS/RTL + XRT 2022.2 | HLS/RTL kernel、U280/U55C/Versal，DDR fallback |
| 控制与统计 | C++ + Python | C++ 正确性/运行时；Python 只做批实验、汇总和制图 |

### 5.3 基准选择

- **学术：** Titan23、Koios、VTR 9 自带异构架构；补充受控的拥塞、长线、高扇出、criticality 和资源比例压力测试。
- **商业：** FPGA 2024 Routing Contest 的 FPGAIF 预放置设计；另收集许可证允许公开的 RapidWright/FPGAIF UltraScale+ examples。
- **多 die：** 公开 VTR 多 die 模型和可获得的 SLR 商业设计；如果商业设计不足，合成拓扑实验只能作为扩展性补充，不能替代真实设计主表。
- **拆分：** 以设计家族而非单个运行随机拆分为 tuning/validation/test；最终 test 在参数冻结后只运行一次主实验。

## 6. 基线可执行性分级

| 等级 | 定义 | 可如何使用 |
|---|---|---|
| B0 同机直接复现 | 代码、版本、输入均可获得，可按相同 QoR 运行 | 主表速度/QoR/能效基线 |
| B1 可信重实现 | 算法细节充分，团队实现并通过作者结果或小例验证 | 主表可用，但标注 reimplementation |
| B2 公开结果引用 | 缺代码/数据/版本或无法合法运行 | 只列相关工作和论文数字，不声称直接击败 |
| B3 工业黑盒 | Vivado 等只能看全流程输出 | QoR/合法性/用户时间参考，不作 kernel 级归因 |

初始分级：VPR 9、RWRoute、RapidWright/FPGAIF 为 B0；CUFR 以仓库实际可构建性确认后进入 B0；Potter、FPGA 2026 页布局、DiffRouter 在代码未确认前是 B2；Vivado 是 B3。每次投稿前重新核验。

## 7. 统一实验原则

1. **等质量比较：** 先筛除非法/失败结果，再在 wirelength 与 CPD 门槛内比较时间/能耗。
2. **完整 wall-clock：** `parse + graph build + host preprocess + H2D + all iterations + timing update + D2H + export + validation`；kernel 时间另列。
3. **复现元数据：** 输入 SHA-256、代码 commit、工具/driver/XRT/platform、bitstream hash、seed、CPU/GPU/FPGA、频率、功率采样方法和原始日志。
4. **统计：** 确定性配置验证 5 次输出一致；时间至少 5 次报告 median、IQR 和 95% bootstrap CI；包含 warm/cold cache 协议。
5. **能效：** 报告 board power、host power（可测时）、joules/design；CPU/GPU/FPGA 均含各自数据搬运。
6. **失败不可隐藏：** route failure、timeout、OOM、fallback 和未收敛均进入主表分母。
7. **参数不泄漏：** 调度/量化参数只在 tuning/validation 选定，test 设计不再调整。

详细模板见 [实验路线与指标模板.md](./实验路线与指标模板.md)。

## 8. 阶段顺序与 go/no-go

本路线不设固定完成年限，采用依赖和证据门控：

| Gate | 完成条件 | 未通过时动作 |
|---|---|---|
| G0 文献/基线冻结 | 矩阵覆盖最近工作；B0/B1/B2分级；工具版本可启动 | 不进入硬件架构设计 |
| G1 数据一致性 | VPR/FPGAIF ↔ SoA ↔ 回写无信息丢失；合法性检查一致 | 修 converter/schema，不优化 kernel |
| G2 软件事务模型 | PersistRoute golden model 合法、确定，QoR ≤2%门槛 | 先修算法；不得用硬件并行掩盖 |
| G3 单PE可行 | cycle model 与板上性能误差 ≤15%，DDR缩小图跑通 | 重构图/队列；必要时降并行度 |
| G4 多PE端到端 | 对强多核 ≥3×，含 PCIe/导出；消融支持 claim | 达不到则缩小 claim 或转 FCCM/FPL/DATE |
| G5 TilePlace独立性 | 对 FPGA 2026 页布局形成算法+硬件双差异 | 不独立则并入 FusionPAR或转应用型工作 |
| G6 RouteCast有效性 | 未见设计上热点相关和最终路由改善同时成立 | 停止高频反馈方向 |
| G7 DieRoute真实性 | 至少一组真实/可信多die数据 + 参数化缩放 | 仅模拟不足以主投 DAC |
| G8 FusionPAR非加和 | 交错协议相对最佳顺序组合仍显著获益 | 不拆成第五篇 |

## 9. 五篇论文防重叠审计

每篇投稿冻结前，由非第一作者依据 [五篇论文创新点对照表.md](./五篇论文创新点对照表.md)逐项签字：

- 与前作在问题定义、伪代码、硬件模块、实验、图表和文字上比较；
- 至少一个新算法机制和一个配套硬件机制；
- 至少一个主要结果无法由前作系统直接产生；
- 所有复用模块在方法图中灰化并明确引用；
- 不以更多 PE、更多 HBM channel、换板或 benchmark 扩充作为主贡献；
- 主张使用“we introduce/first”前逐项查最近两年文献与预印本。

## 10. 近期首要执行清单

1. 固定 VPR 9、RapidWright、FPGAIF、RWRoute、CUFR 的 commit 与许可，形成 B0 构建日志。
2. 下载/申请 Potter、FPGA 2026 页布局、DiffRouter 的全文和代码；在获得前保持 B2，不猜实现细节。
3. 定义 v0 二进制 schema，完成 VPR RR graph 和 FPGAIF device graph 的 round-trip 单元测试。
4. 在 VPR/RWRoute 上 profile：每迭代 frontier、外存访问、bbox、criticality、conflict、route-tree size 分布。
5. 先写 PersistRoute 的确定性 C++ 事务模拟器；以合法性/QoR通过为硬件启动条件。
6. 建立统一 manifest、日志和 metric extractor；先测 VPR/RWRoute/CUFR 的全 wall-clock。
7. 确认 U280/U55C/Versal 可用性；无 HBM 时以 DDR 缩小图证明功能，但在论文主结论前迁移 HBM。

## 11. 本地与在线主要来源

### 本地核心论文

- [RippleFPGA](./论文库/RippleFPGA.pdf)
- [RWRoute](./论文库/RWRoute%20An%20Open-source%20Timing-driven%20Router%20for%20Commercial%20FPGAs.pdf)
- [商业 FPGA 并行路由/CUFR](./论文库/An%20Open-Source%20Fast%20Parallel%20Routing%20Approach%20for%20Commercial.pdf)
- [Ripple（仅 ASIC 加速组织参考）](./论文库/Ripple_A_Robust_and_Effective_Routability-Driven_Placer.pdf)
- [SimPL（仅 ASIC 加速组织参考）](./论文库/SimPL%20An%20Effective%20Placement%20Algorithm.pdf)

### 在线关键入口

- [VPR 9 官方文档](https://docs.verilogtorouting.org/en/latest/)
- [RapidWright 官方文档](https://www.rapidwright.io/)
- [FPGA 2024 Routing Contest](https://xilinx.github.io/fpga24_routing_contest/details.html)
- [AMF-Placer ICCAD 2021](https://doi.org/10.1109/ICCAD51958.2021.9643574)
- [DREAMPlaceFPGA-MP](https://arxiv.org/abs/2311.08582)
- [OpenPARF](https://arxiv.org/abs/2306.16665)
- [RapidLayout](https://doi.org/10.1145/3501803)
- [Potter](https://doi.org/10.1145/3676536.3676783)
- [MultiQueue-Based FPGA Routing](https://www.alex-singer.com/publications/conference-papers/multiqueuebasedfpgarouting/)
- [DiffRouter](https://doi.org/10.1109/FCCM68464.2026.00029)
- [RouterAcc（只借鉴 ASIC 加速机制）](https://past.date-conference.com/proceedings-archive/2026/DATA/72.pdf)

## 12. 最终判断

这五篇方向可以形成一个统一研究计划，但只有在“共享基础设施、隔离科学主张”条件下才合理。近期最大的 novelty 风险不是硬件做不出来，而是 Potter、FPGA 2026 page placement、DiffRouter 和 RouterAcc 已分别覆盖 overlap tolerance、硬件页布局、GPU 商业路由、持久存储/流程协同的一部分空间。

因此主线应从“实现一个更快模块”升级为：

> **用 FPGA 特有的离散架构语义定义事务、状态与闭环，把并行性、持久数据面和端到端 QoR 联立为可验证的新算法—体系结构协议。**

只要每个 gate 坚持负结果也触发停止/转向，五篇将是五个依赖递进但科学问题独立的工作，而不是一套 router 的切片发表。
