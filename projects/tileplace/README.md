# TilePlace 独立工程

时序驱动异构页布局 HLS 原型。`tileplace_kernel` 独立处理 CLB/BRAM/DSP page capacity、region、criticality、固定 tie-break 和确定性 site assignment。当前 cascade 字段已进入接口，连续形状合法化将在真实 benchmark 接入阶段扩展。

普通 C++：`g++ -std=c++17 -O2 -Iinclude src/tileplace.cpp tb/tileplace_tb.cpp -o tileplace_tb`。  
Vitis 2022.2：`vitis_hls -f run_hls.tcl`。

## 当前边界（2026-08-31）

当前代码是独立、可综合的 toy 骨架，不是论文级 placement 系统：固定上限为 512
instances/64 pages，测试只覆盖 8 个合成 instance；尚未读取真实 VPR 网表/站点、
计算完整 net/timing 增量、处理 fixed block 与 macro/cascade 连续合法化，也没有 VPR
placement 写回、CPU 大规模 golden、XRT host 或真实 benchmark 数字。

## 接手后的实现顺序

1. 先保持 kernel 不变，定义 VTR 9 placement 数据契约与带 SHA-256 的 manifest；
2. 实现不限 512-instance 的 CPU golden，验证异构 site、唯一占用、region、fixed
   block、macro/cascade 和确定性；
3. 将输出写回 VPR `.place`，用同一 VPR router 对 legality、routed wirelength、CPD
   和可布通性做 fail-closed 检查，首个真实案例使用 `diffeq`；
4. 再设计 page decomposition、增量 net/timing cost 与并行冲突协议；
5. correctness 冻结后才扩展 HBM ABI、多 CU/XRT、HLS/RTL 和 U280 实现。

强基线首选本机可执行的 VPR 9 placement。DREAMPlaceFPGA、AMF-Placer 必须固定
commit、依赖与命令，并使用同一后端 router 验证后，才能作为可直接比较的结果。
