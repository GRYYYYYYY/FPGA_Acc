# 根时钟与 VPR ignored net 的支持缺口

本文件是独立验证期间对输入失败的只读诊断，不是已实现的支持能力。冻结实验
继续使用原来的拒绝规则，s38584.1 的两个转换失败仍计入完整六设计分母。
原始失败及输入绑定见
[`independent_validation_s38584_clock_failure_2026-10-13.json`](independent_validation_s38584_clock_failure_2026-10-13.json)。

## 已核实的原因

s38584.1 的 packed netlist 根时钟为 `pclk`。RouteCast 端点提取器按明确策略
排除根时钟连接，FP converter 检测到 `excluded_nets` 后拒绝，避免把不完整连接
集合当成完整输入。只删除这个拒绝条件仍不正确：`pin_details` 包含时钟端点，
随后“每个 pre-route sink 都必须具有原生 routed path”的检查也会遇到这类端点。

原生 route 中共有 13 个 `global net connecting` 段落：`pclk`、`pg32454`、
`pg34597`、`pg24151`、`pg34232`、`pg33948`、`pg33949`、`pg33946`、`pg33947`、
`pg33945`、`pg33950`、`pg32429`、`pg25583`。不能凭这个文本标签把全部网络
都解释为时钟或随意删去；额外十二个网络的具体类别尚未在本阶段逐一判定。

VPR 的
[`read_route.cpp`](../../tileplace/third_party/vtr-verilog-to-routing-8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07/vpr/src/base/read_route.cpp)
在 `net_is_ignored(net_id)` 分支生成这些段落，不输出 RR 路径。每个成员行记录
block 名称、ID、`(x,y,layer)` 和 pin class；第三个坐标不是 subtile。
读入时会要求该 net 被标记为 ignored，再调用 `process_global_blocks`。

当前 PR 的
[`parse_original`](../../persistroute/tools/write_vpr_route.py)
把这类段落保留为不匹配普通 routed-net 正则的原始文本。FP 的
[`validate_candidate.py`](../tools/validate_candidate.py)
仅替换有生成路径的 net，其余段落原样复制。这对有移动的 ignored-net 成员
不能直接成立：成员坐标、物理 pin class 可能需要随 placement 更新。

## 不能只依赖原生成功标记的地方

当前冻结 VPR 的 `process_global_blocks` 核对 block 名称与 ID、x/y 坐标，以及
pin class 是否落在该 block 的合法范围内。该函数解析 layer 但此处坐标比较
只比较 x/y；此处也没有完整比较 net 的源/汇成员多重集合或精确 pin 身份。
这描述的是该函数的检查范围，不代表对整个 VPR 的全面缺陷审计。

因此未来 FP 接入不能只修改原始文本并等待原生工具返回成功。它需要独立核对
成员是否完整、是否重复、是否属于对应 net，以及 layer、端口/位号、物理类别
与候选 placement 是否一致。保留现有 fail-closed 行为比静默丢弃这些信息正确。

## 后续实现的必要边界

1. 为 native ignored nets 建立显式、输入哈希绑定的静态契约，保留 net 身份、
   原生分类、全部源/汇的逻辑身份与物理映射。区分根时钟与其他 ignored net；
   尚未识别的类别继续拒绝，不能把“没有 RR 路径”等同于“没有连接”。
2. 保持 PR 的任务集合只包含需要 RR 搜索的连接，同时说明 omitted-from-search
   与 omitted-from-design 的区别。静态网络仍须进入转换完整性和发布前检查。
3. 根据候选 placement 重新生成 ignored-net 成员行；保留原生 net/block ID、
   正确 layer 和物理 pin class，独立比较完整源/汇集合后再调用原生 validator。
4. 核对 STA/criticality 导出对 ignored nets 的处理，证明采用的是目标 VPR
   架构的全局网络语义。不能声称实现了物理时钟树布线、时钟网络容量优化或
   跨区域时钟约束，除非有相应数据与检查。
5. 添加缺失/重复成员、错误 net/block/pin 身份、错误 layer/坐标的拒绝用例；
   用一个真实移动证明原生闭合与成员回写，再验证无 global-net 输入保持旧语义。

实现必须等本轮冻结实验终止后开始，并作为新的开发阶段归档。不能回写或
覆盖本轮失败，也不能继续把已经用于诊断和修复的设计称为新策略的 untouched
验证集。是否扩大到其他原生网络类别，需由真实输入证据决定。
