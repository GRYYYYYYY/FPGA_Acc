# 最小见证及适用范围

生成器在 `../code/pr0.cpp` 的 `synthetic` 和 `shared_trunk`；生产函数直接链接，宽参考由固定源码机械生成。`witnesses.csv` 保留16项边界／事件记录，`shared_trunk.json` 是补充的真实不同sink测试。数值可由代码重建，不上传任何旧设计原始RR图。

主要四节点图：边0→1、0→2、1→3、2→3，base=1、delay=0；net=7、source=0、sink=3，criticality=0、max_hops=65535、seed=(0,0,0)。所有初始occupancy=0、capacity=1、version=0、owner=INVALID；节点1 history=3、节点2 history=9，其余成本0。初始选0→1→3，成本5。

| 事件 | 精确变化和结果 | 见证类别 |
|---|---|---|
| off_path_decrease | 节点2 history 9→0，version+1；旧路径仍容量合法，P/N接受，但S选0→2→3、成本2 | 新鲜度／串行等价差异；不是状态破坏 |
| off_path_increase | 节点2 history 9→20，version+1；S仍旧路径、成本5，F保守失效 | 此数值图上的多余失效；不是一般单调性定理 |
| on_path_version | 节点1 version+1而成本/占用不变；P拒绝，N接受 | P/N合同差异 |
| other_net_full | 节点1 occupancy=1、owner=9、version+1；P拒绝、N允许中间超用 | 当前路径容量反例；不等于最终路由失败或硬件错误 |
| same_net_owned | 节点1 occupancy=1、owner=7、version+1；P绕过版本拒绝，不再次增加同net占用 | 单owner表示下的共享语义 |
| ripup_decrease | 基于图令节点2原occupancy=1、owner=9、present=20；事件将occupancy归0、owner=INVALID、history归0、version+1；S改道、P/N仍收旧路 | 合成rip-up事件，不称历史轨迹 |
| tree_seed_change | 节点1设置owner=7、occupancy=1；seed改为(1,1,0)；S分支1→3成本1；P/N不能单靠读集发现树身份变化 | 旧事务失去当前树身份绑定；不是合法控制器实际运行中的错误证据 |

不同sink共享trunk：图0→1、1→2、1→3。第一次net7路由0→1→2；第二次使用权威seed树{0,1,2}，路由1→3。两次提交status=4，trunk占用1、owner7，独立四副本一致。原 `same_net_repeat` 仅测试同一分支重复提交；不能冒充这个多sink测试。

边界记录：

- `failed_rollback` 在合法前缀后附越界节点100，整笔拒绝且四副本保持原值。没有写入再补偿。
- `integer_commit_boundary` 明示 occupancy=65535 时饱和、version=UINT32_MAX 时按无符号数回绕0。四副本相同不证明无限占用或无限版本寿命正确；该压力输入不在本轮真实控制器采样范围。
- `cost_saturation` seed成本UINT32_MAX−1，两个base=1的边，结果饱和UINT32_MAX。
- `path_pool_boundary` 3节点链、容量1，生产返回3；不推断不可达。
- `full_read_boundary` 0连1…65535，1→65536→65537，末边base100，其余base1；窄完整记录guard失败，宽参考成本102。宽依赖包含根的path-version读；旧探索读集的基数概念不同。
- `queue_boundary` 同图每bank深度1，观察到 push 失败；不是“图不可路由”。
- `path_count_boundary` 65536节点链，max_hops65535，包含attachment的路径有65536项，生产16位路径计数失败、宽参考成功。
- `unreachable_known_graph` 无边二节点，源0、汇1；在这个已知小图可以判不可达。不能据此给旧status3批量标不可达。

无重复确定性差异见证：32个真实查询同快照重跑一致；这是有限观察。原提交ABI的32位offset加法潜在回绕只作源码边界记录，未以非法巨大指针运行，不能宣称恶意输入安全。所有小图均是CPU见证，未运行RTL。

CSV的容量/算术/不可达记录未执行commit，其 `F_valid/P_status/N_status/PN_state_consistent` 是原生成器占位列，不能读成提交成功；逐行适用性见 `column_scopes.json`。其余记录的状态一致性来自实际CPU调用。
