# 有限诊断结果

运行前提交：`027f0107ee623441689621d3283fa1c812b2b69f`。协议 SHA-256：`889be475ed327e5072e4c781f065fdf096b512a74b8e03db4bfed1318bb12208`。源码审查基准 `b32afa4303a5574dde7171b4ae6e3d07aeb8a06c`，已接受审计 `ec1c5634ea9cbb6f8baf55e94c75cff988bb7b16`；本轮七文件 CPU 指纹 `f8d785d370921d232653d59055df3269c8fa94e2db22c8b92a4ce2ce374eee24`。历史 Git source commit 仍为 unknown。

共 6 warmup、18 正式计时、1 baseline smoke，全部完成；执行失败 0、超时 0、未启动 0。24 次 TP 进程共执行 512 次 native closure，三个设计均已暴露，不能称 holdout。没有自动重试、换参数或追加案例。

| 开发案例 | A prefix 开启中位数 / s | B 关闭中位数 / s | B/A | CPD / ns（两臂相同） | WL（两臂相同） |
|---|---:|---:|---:|---:|---:|
| diffeq | 71.384 | 103.907 | 1.456× | 6.59759 | 9098 |
| clma | 379.337 | 645.805 | 1.702× | 11.5929 | 79926 |
| spla | 238.923 | 395.851 | 1.657× | 7.64733 | 36373 |

A/B 仅切换既有 pressure-prefix；同一 generic-indexed-port-v1 parser、控制器、输入、seed 1、channel width 200、4 epochs、最多 24 closure、CPU31/单 worker。所有 source/input SHA 与冻结版本一致，实际开关与标签一致。每例三对，以上为每臂中位数之比；每对原始比值在 `evidence/pilot/derived_summary.json`。样本量和共享主机不足以支持普遍性或稳定统计显著性。

## 全部时间样本

| 案例 | 类型/对号 | 顺序 | A / s | B / s |
|---|---|---|---:|---:|
| diffeq | warmup 0 | AB | 72.140226 | 104.588177 |
| diffeq | measured 1 | AB | 71.430711 | 103.196248 |
| diffeq | measured 2 | BA | 71.383645 | 104.538798 |
| diffeq | measured 3 | AB | 71.343511 | 103.906916 |
| clma | warmup 0 | AB | 386.399850 | 625.066298 |
| clma | measured 1 | AB | 390.906359 | 627.221746 |
| clma | measured 2 | BA | 377.489273 | 662.718634 |
| clma | measured 3 | AB | 379.336520 | 645.804936 |
| spla | warmup 0 | AB | 235.919948 | 403.118072 |
| spla | measured 1 | AB | 238.922895 | 395.851178 |
| spla | measured 2 | BA | 235.467372 | 391.146134 |
| spla | measured 3 | AB | 239.926874 | 402.355371 |


基线 smoke 外层 2.017749 s。原始命令、终态、loadavg、report/timing/原生 JSON 在 `evidence/pilot/<run_id>/`。失败/超时计数为零，不代表删除了失败；历史四个输入失败仍保留在 `all_cases.csv`。

## 总成本与计时树

warmup 1827.232570 s；18 次正式计时 5512.947121 s；baseline 2.017749 s。新实验进程墙钟合计 **7342.197441 s（2 小时 2 分 22.197 秒）**。监督器总经过时间 7342.769503 s，包含逐次离线签名核对 0.206682 s 和调度/进度写出；未用满 3 小时 pilot 上限。后续整理、独立离线审计与本轮算法运行时间分开，不伪装成 cold-deployment 时间。

下表每行取一条真实完整运行，不把不同样本的阶段中位数拼接。单位秒；完整精度见 CSV，表内舍入可能产生 0.001 秒差。

| 实际样本（A 的中位数那一次） | 外层总计 | 准备 | proposal | oracle_driver | 反馈 | search_other | 写出 | 外层未归因 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| diffeq_measured_2_A | 71.384 | 0.545 | 50.301 | 19.566 | 0.416 | 0.325 | 0.126 | 0.104 |
| clma_measured_3_A | 379.337 | 2.517 | 214.924 | 140.571 | 18.277 | 2.484 | 0.450 | 0.113 |
| spla_measured_1_A | 238.923 | 1.336 | 161.265 | 69.534 | 5.236 | 1.176 | 0.236 | 0.141 |

| 案例 | proposal 占总时间 | native VPR 子计时 / s | 拒绝 trial / 全部 | 被拒绝 trial 的 oracle_driver / s | pressure 查询 | net-cache 命中率 | 索引/快照 setter / ms | cache 失效 / ms | proposal 无限加速上界 |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| diffeq | 70.47% | 17.173 | 15/16 | 18.370 | 21,062,020 | 99.566% | 0.207 | 0.864 | 3.386× |
| clma | 56.66% | 131.276 | 15/24 | 89.114 | 64,461,504 | 99.358% | 6.255 | 3.981 | 2.307× |
| spla | 67.50% | 64.078 | 19/24 | 54.831 | 53,947,702 | 99.705% | 1.694 | 1.857 | 3.077× |


native VPR 是 oracle_driver 的子计时，不能重复相加。索引/快照 setter、cache 失效也是嵌套诊断计时。43 个历史/新运行的外层互斥分区求和核验通过；没有按拒绝比例摊派共享 proposal 时间，拒绝成本列只指精确匹配到相应 trial 的闭环驱动成本。总时间仍包括全部 proposal 和所有拒绝。

proposal 包括生成、排序和评分；缺少更细的独立 scorer timer。因此上界只是消除整个 proposal 的乐观界限，不是新机制的可达加速。现有 net-cache 已有极高命中率，不能据此承诺再加同类缓存有收益；pressure 查询的唯一键比例与新依赖维护成本尚未测量。

## 正确性与独立复核

8,000 次运行前压力求和检查通过。全部 24 个 TP 运行的 512 份 native receipt 保留；每例 4 个 B 结果与非空 A 参考对照，共 256 个跨臂提交候选比较。所有提交给 native 的 placement SHA、transaction 整数 cost、阶段/决策、数值反馈与 parser、最终合法性及精确 CPD/WL 一致。最终输出文件同时绑定 native 输入 SHA，逐块坐标/类型字段核对相同。VPR 重写路径表头、注释分隔符及 tab padding，不被当作算法差异。

内部未提交 native 的枚举候选没有完整逐项 trace，只保留 phase 计数；不宣称穷举内部状态等价。未来有状态依赖复用需要更强的全候选签名。`verify_compact.py` 从小型原件重新生成签名并复算统计；`validate_delivery.py` 另外检查服务器原始候选/结果与冻结 Git 版本。见 `evidence/compact_validation.json`、`evidence/delivery_validation.json`。

spla 与历史 2fa6 实现的记录轨迹、cost、反馈及 QoR 相同，但历史一次 328.270 s 与本轮 warmup 235.920 s 不同。原因未直接测量，不能从跨日期时间差推导 prefix 收益；保留 `evidence/spla_historical_trace_crosscheck.json`。

## 准备成本和基线

本轮新测的是 refinement-only。历史 spla 的方法专有准备为 37.448271 s，共同初始 native 阶段 12.785410 s，两次 refinement 分别 328.270379/330.285928 s，驱动未归因 2.524694 s，批次总计 711.314682 s。历史方法准备加第 0 次 refinement 为 365.718651 s，只是历史组件账目，不是新外层 cold timer；不得把批次除二，也不得加到本轮 238.923 s 来声称新 cold 时间。diffeq/clma 的历史准备钟及部分历史输入生成器身份仍不完整。

基线确实支持 `--read_initial_place_file` 后 fresh-SA reanneal，不恢复温度/RNG/route checkpoint。diffeq smoke 的总时间 2.017749 s，native 1.699172 s，其余准备/检查/写出/启动 0.318577 s。合法，CPD 6.61216 ns、WL 9097；共同起点为 6.59759 ns、9103，TP 为 6.59759 ns、9098。SA 结果未满足 timing-first 接受门槛，必须保留 B0 incumbent。既不能用 2 秒与 71 秒宣布同质量加速，也不能由这次不被接受的 SA 结果宣布 TP 等预算胜出。预算循环、质量—时间曲线和未见设计仍未验证。

结论：REVISE_ONE_HYPOTHESIS。prefix 的现有工程收益成立；只保留固定反馈周期内依赖校验的候选评分项复用这一待证假设，见 `NEXT_GATE_DECISION.md`。不启动第二轮搜索或正式矩阵。
