整数接口组合：批量完整身份编码→transaction13 冲突选择→整批原子位置提交。输入是已评分、已完成 per-unit best 与去重的候选描述符及 conflict ranges；这些前序阶段尚未组合到本接口。输出 stage/status 定位失败，位置只在提交阶段完整验证后修改，scratch 失败需丢弃。25 个 CPU 用例验证五种类型名称与三阶段故障、共享 net 冲突，未验证五类枚举语义或全搜索。尚未 RTL/native 接入。

`rank_commit_words.hpp` 进一步组合已有 transaction13 的 per-group best（含 forbidden）、稳定身份去重、冲突选择和原子位置提交。最终 selected 索引映射回原始候选。6 个 CPU 用例通过，覆盖重复身份最低分、禁用、共享网络冲突以及 best/select/commit 阶段失败位置保持。此入口接收已有完整身份与评分，不含枚举、评估及身份构造；尚未 RTL/native 接入。

随机组合差分：2000 批 × 12 候选 × 3 组，独立 tuple/map/set 参考验证 best、forbidden、stable dedup、net/unit 贪心冲突、原始 selected 索引与提交后完整位置数组。输入是单成员单位身份，没有 site 冲突，不能据此宣称全枚举或全搜索验证。严格 Werror 编译及运行通过。

`encode_rank_words.hpp` 将描述符身份构造与完整 rank/select/commit 相连，并根据同池描述符索引构造 forbidden。30 个 CPU 用例覆盖五种身份名称、共享网络冲突、三阶段失败位置保持及禁用过滤。groups 需排除仅用于 forbidden 的占位描述符。输入 score 仍来自外部，未包含枚举/评估，也未完成此入口的 RTL/native 验证。

评估与控制串联验证：1000 批独立解析 HPWL/Q20 参考，evaluate_batch 输出直接交 encode_rank，检查禁用过滤、selected 和最终位置。另验证 7 个容量/超宽 ID/未知 block/重复 trial/负权重错误，以及合法 guard 拒绝；失败输入位置保持。限定两 block 单成员 move 的 CPU 场景，未包含枚举或全路径 RTL/native。

整链 CPU 验证：两组冻结 Python 五类枚举参考共 16 个有序 trial，逐字比较类型/owner/trial；实际串联枚举→评估→身份→best/dedup→conflicts→commit。独立解析 all-block HPWL 验证 singleton 无收益，macro 平移到 x2/3 被选中、score -419431 和最终位置正确。仅 1D、单 owner group、一个 net、零 timing/congestion 权重，不能外推完整 native 或 RTL 验证。

`enumerate_color_words.hpp` 按外部 eligible 顺序枚举多单元，输出独立 group 范围，固定单元保留空 group。两个三成员 macro 单元的候选完整内容和边界与旧 callback 枚举一致；group 容量及非法 eligible index 在发射前拒绝。仅 CPU 适配差分，尚未组合 eligible 计算或完整颜色评估提交；参考共享原分支算法。

颜色整链 CPU 验证：实际 eligible(color0)→3 个 singleton 或 2 个 macro groups→评估/身份/best/dedup/冲突/提交，两场景各无禁用/有禁用共4次。宏场景解析预期最佳 index2，禁用后回退 index6；共享 net 只提交一个，最终位置正确。首 owner 冻结 Python trial 对比保留；其他 owner 未独立 Python 逐项对比，尚未完整统计或 RTL/native 验证。

颜色统计：rank Result 增加 dedup 后 proposals；color_stats 输出 eligible、proposals、accepted、rejected、5 种 accepted kind 数。4 个整链用例验证宏场景 2 proposals/1 accepted/1 rejected；2000 批独立 map 参考验证 proposals 基数。原冻结 RTL 包保持原源码，不代表此统计扩展已 RTL 验证。

`full_color_words.hpp` 提供通用 CPU input/scratch 入口，完整调用 eligibility、multi-group enumeration、batch evaluation、identity/rank/select/commit、stats。4 个参考场景与逐步路径及解析预期一致。含指针结构体仅用于 CPU orchestration，不是 HLS 顶层；硬件需展开显式 AXI 参数。forbidden indices 仅引用当次枚举，尚不支持外部身份池，也未 native 接入。

外部禁用身份：full_color 支持独立 ExternalForbidden 池，以完整 kind/member/trial 内容跨池相等比较，先验证 ranges 再将匹配评分置零。4 个整链场景验证与索引禁用相同的回退与统计，外部池拥有独立 backing。CPU-only；canonical/backing/nonalias 由调用方保证，新增 malformed/四维差异测试和 native/RTL 尚未完成。

外部池边界 CPU 验证追加12例：不同池偏移仍匹配；x/y/subtile/layer 位差（含符号极值）、成员或 kind 差异均不匹配；非法 kind/member/trial 范围、超宽源 ID 和缩放溢出在评分写入前拒绝。严格 Werror 编译与运行通过，仍未 RTL/native。

`host_propose.hpp` 在私有位置副本上运行完整整数颜色入口，把 selected 描述符解码成原 Proposal（kind/units/trial/score/write_sites/touched_nets）及统计。4 个测试场景验证输出与输入位置不变。仍未接 native server/VPR；容器只在 host 协议边界使用。
