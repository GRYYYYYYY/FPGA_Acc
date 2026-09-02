# TilePlace claim matrix

| Claim | Current evidence | Status | Remaining work |
|---|---|---|---|
| Real VPR legality and heterogeneity | Five-case correctness matrix; 2866 blocks; Koios CLB/DSP/memory/IO and 43 macros | Proven | None for CPU correctness |
| Native region/fixed constraints | Two official VTR XML cases and fail-closed recovery; separate post-freeze apex4 point preserves 28 coordinate-fixed I/O and closes natively, with retained +0.210% WL/+0.463% CPD | Proven for legality and one separately reported QoR point | Add a constrained suite before making aggregate constrained-QoR claims |
| Deterministic page transactions | 1/2/4/8 fork workers exactly match serial on four cases; disjoint site/net commit; macro atomicity | Proven on current cases | C++/shared-snapshot implementation for actual scaling |
| Connection-specific timing is necessary | Net-level and unguarded connection-star diffeq ablation both regress CPD | Proven on diffeq | Broader timing-model ablation |
| Critical-distance guard controls timing risk | Diffeq CPD regression removed; nine-case/two-architecture-family CPD geomean -1.010%, worst +0.017%; all four post-freeze cases and the macro-stress case are non-regressing | Supported | Pre-register tolerance on a broader suite |
| Routed wirelength improves | Nine-case geomean -0.088%, worst +0.439%; post-freeze quartet geomean -0.015%; Titan23 neuron is retained at +0.088%; macro-stress conv_layer -0.124% | Supported only in aggregate, and small | Broader matrix; congestion-aware cost |
| Better than executable VPR cluster-level AP | Same packed netlist/router on the original six-case subset; AP is +3.711% WL/+16.103% CPD geomean while TilePlace is -0.071%/-0.300% vs conventional SA | Proven for this experimental six-case VPR AP path | Do not generalize to attention_layer or external timing-driven placers |
| Better than independent placers | DREAMPlaceFPGA `0044943...` and AMF-Placer `70d9828...` source/CLI audits are archived as B1 candidates, but both change the netlist/architecture/backend methodology | Not supported | Use a separately pre-registered Bookshelf/FPGAIF/Vivado cohort; do not merge it into the same-packed-netlist VPR matrix |
| Endpoint timing coverage | Main nine cases: 198595/198595 clustered and 194155 atom mapped, with 4440 explicit conv_layer unmapped rows; separate apex4 constrained point maps 2263/2263 at both levels | Proven with explicit distinction | Extend constrained timing coverage beyond one point |
| CPU runtime is bounded | Six-case medians 0.545--59.672 s; full samples and variability archived; spmv/softmax CV 2.8%/2.2% | Proven for Python reference | Add larger architecture families |
| CPU parallel speedup | Controlled clma 1/2/4/8 process results show no speedup | Not supported | Replace Python IPC with C++ or HLS dataflow |
| FPGA acceleration | HLS kernel is still a bounded toy and is not the research CPU algorithm | Not supported | Freeze algorithm, redesign ABI, HLS/RTL/XRT, physical U280 runs |
