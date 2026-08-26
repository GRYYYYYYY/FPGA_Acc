# TilePlace 独立工程

时序驱动异构页布局 HLS 原型。`tileplace_kernel` 独立处理 CLB/BRAM/DSP page capacity、region、criticality、固定 tie-break 和确定性 site assignment。当前 cascade 字段已进入接口，连续形状合法化将在真实 benchmark 接入阶段扩展。

普通 C++：`g++ -std=c++17 -O2 -Iinclude src/tileplace.cpp tb/tileplace_tb.cpp -o tileplace_tb`。  
Vitis 2022.2：`vitis_hls -f run_hls.tcl`。
