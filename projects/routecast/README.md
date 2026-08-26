# RouteCast 独立工程

增量 FPGA RR routing-sketch HLS 原型。接口显式包含 segment class、direction、pin class、capacity 和 dirty connection，只更新受移动影响的连接。当前是有界 hop 贪心 sketch，不输出精确 route。

普通 C++：`g++ -std=c++17 -O2 -Iinclude src/routecast.cpp tb/routecast_tb.cpp -o routecast_tb`。  
Vitis 2022.2：`vitis_hls -f run_hls.tcl`。
