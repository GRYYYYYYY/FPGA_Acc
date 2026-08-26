# FusionPAR 独立工程

共享状态的原子 placement move + incremental route transaction + repair 生成原型。版本不匹配或容量冲突不会部分修改状态；高 detour 可在提交后生成局部 repair，sketch overflow 可在精确路由前拒绝。

普通 C++：`g++ -std=c++17 -O2 -Iinclude src/fusionpar.cpp tb/fusionpar_tb.cpp -o fusionpar_tb`。  
Vitis 2022.2：`vitis_hls -f run_hls.tcl`。
