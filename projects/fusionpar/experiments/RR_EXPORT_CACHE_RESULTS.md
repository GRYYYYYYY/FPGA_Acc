# FusionPAR 原生导出元数据复用

本阶段优化重复 RR XML 解析，不改变 C++ 搜索、候选生成、QoR 门槛、事务提交或
原生合法性/STA。缓存是公共转换基础设施，不能作为 FusionPAR 的独立算法贡献。

`--rr-export-backend sqlite` 在转换阶段为导入的完整连续 CSR 生成只读数据库：
保留全部节点的坐标、layer、类型、ptc、逻辑 pin，以及每个边对的原始 switch
和所有歧义 switch。生成后对全部节点、边对与原 XML decoder 做往返等价检查。
不完整/越界的 CSR 被拒绝。该格式不是 RR 图压缩或 FPGA/HBM ABI。

数据库和 graph/source SHA 由 bundle 绑定；每个候选处理前后仍核对文件哈希。
运行时采用 read-only SQLite lookup，缺少节点、边或身份不匹配都失败，不回退
到另一套语义。没有使用到的歧义边不会误拒绝其他合法路径；用到歧义边仍与
XML 方式一样拒绝，不能任选一个 switch 后发布候选。

`costs.json` 在 XML 路径记录 `rr_graph_decode`，缓存路径记录
`rr_metadata_lookup`；其余阶段和检查保持原样。缓存保持 opt-in，默认仍为 XML。

## 验证与费用范围

- CTest 3/3 通过：原 113 项 C++ 核心检查，以及 6 个 Python 缓存用例。
  用例覆盖完整/稀疏查询、pin/layer、并行 switch、缺失记录、错误身份/schema、
  文件 URI 特殊字符、禁止覆盖及无效 CSR。
- 真实 ex5p pilot 的 27,436 个节点、278,974 个边对完整生成并校验；同一真实
  候选的 state/place/route、QoR、criticality、连接 delay 和 timing CSV 字节一致。
- 对一次性副本分别注入 checksum、图身份、节点缺失、边缺失、switch 歧义五种
  损坏，native adapter 全部拒绝，无成功证书，候选与原始成功归档保持不变。

配对协议见 [`rr_export_cache_protocol_2026-10-13.json`](rr_export_cache_protocol_2026-10-13.json)。
ex5p、alu4、misex3 各使用 XML/SQLite 两后端、shared batch/interleaved 两模式，
三个 primary 预算、每组五次。每个 backend/design 只准备一次 bundle，完整准备
时间等额计入该组每次 charged time，包括首次解析、建库和全部往返校验。
这些不是五次独立准备测量。运行成本、含准备成本分别报告，不能忽略缓存首次费用。

独立状态审计与候选文件比较在测量全部结束后执行；不与被计时的 host 运行并行。
所有运行保持默认时序权重 0，并须复现原先同模式的状态、事件和 timing 轨迹。

## 完成结果

60 次运行与六份独立状态审计全部通过；90 对原生验证的七类文件共 630 次
SHA-256 比较均相等。完整最终状态、事件、timing 轨迹同时复现旧 XML 归档。
共 40 次 QoR 提交、80 次拒绝和 100 次 timing barrier；缓存没有改变接受结果。
原始绑定与逐次样本见
[`rr_export_cache_status_2026-10-13.json`](rr_export_cache_status_2026-10-13.json)。

下表为五次运行中位数，单位秒；含准备时间列把该 backend/design 的一次完整
准备费用计入每一个样本。shared batch 一次验证整个移动批，interleaved 逐候选验证。

| 设计 | 模式 | XML host | SQLite host | XML 含准备 | SQLite 含准备 |
|---|---|---:|---:|---:|---:|
| ex5p | shared batch | 5.962 | 4.606 | 8.408 | 9.472 |
| ex5p | interleaved | 12.649 | 9.520 | 15.095 | 14.387 |
| alu4 | shared batch | 7.061 | 5.089 | 9.937 | 12.136 |
| alu4 | interleaved | 14.562 | 10.600 | 17.438 | 17.647 |
| misex3 | shared batch | 6.397 | 4.768 | 9.103 | 10.848 |
| misex3 | interleaved | 13.454 | 9.739 | 16.159 | 15.820 |

| 设计 | 覆盖节点 | 覆盖边对 | 数据库字节 | XML 完整准备(s) | SQLite 完整准备(s) |
|---|---:|---:|---:|---:|---:|
| ex5p | 27436 | 278974 | 4878336 | 2.446 | 4.867 |
| alu4 | 37838 | 403206 | 7139328 | 2.876 | 7.047 |
| misex3 | 32920 | 344820 | 6017024 | 2.705 | 6.081 |

三图没有歧义边对；歧义处理由合成测试和真实 adapter 损坏负例覆盖。生成阶段
的完整往返比较仍检查所有节点、边对，没有用查询覆盖率替代完整覆盖。

缓存降低了这些样本的 host 时间，但初始费用使三个短 batch 的含准备总时间
全部增加；alu4 的三个候选交错模式也略增。当前证据不支持统一端到端加速，
默认继续使用 XML。较长会话可能摊薄建库费用，这是待测推断，不能外推本表。
该优化不构成融合算法收益或 FPGA 性能证据。
