候选完整身份的整数编码

`identity_build_words.hpp` 将五类枚举类型、最多三个 moved unit 的完整成员列表、按 ID 排序的三字位置记录编码为六字身份和独立输出池。单位按完整成员词典序排序，不依赖 unit index；四维坐标逐位保留。成员池复用输入，输出 kind/unit/trial 池从零开始，组合多个候选时需重定位范围。调用方保证数组 backing、无输入输出别名以及合法成员归属。失败在写输出前返回。

CPU：3000 个独立 nested-vector 参考与 7 个原子失败用例通过，严格告警编译通过。尚未 RTL 验证、接入 best/dedup 或完整组合内核。

`batch_words.hpp` 接收六字描述符（score、kind、owner range、trial range），生成共享池七字候选，可直接交给 word best 和 dedup。批次失败需丢弃全部 scratch，已完成的前序记录可能已写入；容量按 kind 字节、unit 记录、trial 记录计算。1000 批 × 12 候选独立 tuple/map 参考验证了完整身份、禁用过滤、每组最优和稳定去重。尚未接入 native VPR 或 RTL，也未组合评估、冲突选择和提交。
