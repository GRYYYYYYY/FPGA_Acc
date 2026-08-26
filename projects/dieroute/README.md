# DieRoute 独立工程

多 die/SLR SLL 预留和 HBM-die queue 映射原型。kernel 按 capacity、delay、criticality、history 选择 boundary，更新版本化 shadow summary，并依据队列负载决定任务归属/迁移。

普通 C++：`g++ -std=c++17 -O2 -Iinclude src/dieroute.cpp tb/dieroute_tb.cpp -o dieroute_tb`。  
Vitis 2022.2：`vitis_hls -f run_hls.tcl`。
