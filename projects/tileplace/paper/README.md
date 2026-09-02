# TilePlace paper evidence

当前论文材料以 VPR 9 placement 为输入基线，并用同一精确 VTR commit、seed、channel
width 和串行 router 对 refinement 前后做 route+analysis。核心入口：

- `RESULTS.md`：可直接引用的结果表、消融与边界；
- `CLAIM_MATRIX.md`：每项 claim 的证据和未完成项；
- `PAPER_DRAFT.md`：当前方法与结果正文草稿；
- `../experiments/timing_titan_extended_matrix_2026-09-01.json`：九案例、两个 architecture
  families 的 timing QoR，含四个 post-freeze validation cases 与一个 previously-probed
  macro-stress case；
- `../experiments/timing_macro_extended_matrix_2026-08-31.json`：加入 conv_layer 后的八案例
  历史基矩阵；
- `../experiments/timing_extended_matrix_2026-08-31.json`：加入 attention 后的七案例
  严格 timing-export 基矩阵；
- `../experiments/timing_multicase_matrix_2026-08-31.json`：扩展前冻结的六案例基矩阵；
- `../experiments/attention_layer_input_capture_2026-08-31.json`：新增 Koios 案例的
  RR graph、connection、timing 与 binary provenance；
- `../experiments/conv_layer_input_capture_2026-08-31.json`：macro-stress 案例及显式
  atom timing-pin mapping coverage；
- `../experiments/titan23_neuron_input_capture_2026-09-01.json`：第二架构族 Titan23 neuron 的
  RR graph、connection、timing、macro 与冻结输入 provenance；
- `../experiments/constrained_qor_matrix_2026-09-01.json`：单独预注册的 apex4 fixed-I/O
  constrained QoR 点；28 个 fixed I/O 保持，WL/CPD +0.210%/+0.463%，不并入主 aggregate；
- `../experiments/timing_guard_ablation_2026-08-31.json`：diffeq timing 消融；
- `../experiments/page_size_ablation_2026-08-31.json`：2×2/4×4/8×8 page 消融；
- `../experiments/cpu_runtime_matrix_2026-08-31.json`：单核 CPU runtime；
- `../experiments/runtime_guard_elision_ablation_2026-08-31.json`：实现热点消融；
- `../experiments/parallel_proposal_matrix_2026-08-31.json`：并行 proposal 等价性与 scaling 边界；
- `../experiments/page_incremental_probe_2026-08-31.json`：Koios macro 与外部约束探针。

所有现有数字都是 CPU placement + VPR 原生验证，不是 FPGA 上板速度、功耗或能效。
