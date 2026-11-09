# TilePlace paper evidence

> **2026-10-13 completion objective:** Finish TilePlace verification and adoption,
> then produce a DAC manuscript from the verified results. See
> [COMPLETION_GATES.md](COMPLETION_GATES.md) for the implementation and paper
> acceptance criteria. The IEEE working manuscript includes the full-color
> RTL work but is not a final hardware-results paper. DAC 2027 rules currently
> require an IEEE template and a 6+1 page budget; target year/track and final
> experimental acceptance remain open.

The new IEEE working manuscript is [`dac2027/main.tex`](dac2027/main.tex).
It integrates the full-color hardware method, the source-sealed 13-case CPU
cohort, baseline functional coverage, and failed timing experiments. Its
claims explicitly retain the open timing/adoption gates. The previous ACM
manuscript remains under `dac/` as historical material.

Build the IEEE draft from the TilePlace directory after loading TeX Live:

```bash
make -C paper/dac2027
```

The PDF and build receipts are in
`work/dac_completion_2026-10-13/ieee_rewrite_build/`. The Makefile uses the
locally extracted Courier fonts in `work/dac_completion_2026-10-13/texmf`;
`LOCAL_TEXMF` can select an equivalent font installation on another host.
Unmodified IEEE class/style files and their archive provenance are retained
in `dac2027/`; `claim_bindings.json` identifies this draft's evidence snapshots.
These build instructions do not establish project completion or submission
readiness. Regenerate the cohort and OOC tables before revising their claims.

Source-backed preparation for the full-color hardware section is in
[HARDWARE_METHOD.md](HARDWARE_METHOD.md). It distinguishes a color invocation
from the host/VPR oracle, and logical AXI bundles from physical HBM mapping.
The corresponding working LaTeX section is
[`dac/hardware_method.tex`](dac/hardware_method.tex). Its standalone IEEE
preview compiled to two pages with embedded fonts and no overfull boxes or
unresolved references; receipts are in
`../work/dac_completion_2026-10-13/hardware_method_preview/`. It is not yet
included in the legacy main manuscript, and its source bindings must be
updated when a final candidate is adopted.

`python3 paper/prepare_ooc_table.py` (from the TilePlace directory) regenerates
`generated/ooc_experiments_table.tex` and its provenance JSON from eighteen terminal
October 12--13 experiments. It rechecks frozen inputs, prerequisites, terminal
receipts, all seven implementation outputs and report contents. Failed timing
rows are retained. This is an internal OOC experiment table; live candidates,
functional adoption and physical-board results are outside its scope.

`python3 paper/prepare_hardware_characterization.py` rechecks the baseline's
complete RTL output arrays and routed evidence before extracting resource
counts and fixture simulation cycles. It creates
`generated/baseline_fixture_cycles_table.tex` and
`generated/baseline_characterization_metadata.json`. These cycle counts use
the generated AXI simulation model and are not physical-device latency.

> **2026-09-29 provenance audit:** A full diffeq timing replay does not reproduce
> the archived V4 trajectory. With the same hashed timing report, the current
> port parser yields 52 initial edges instead of 37. Four development summaries
> plus pdc/dsip disagree with the current parser and match a diagnostic
> restricted-port variant. Archived QoR values remain intact, but the
> single-frozen-implementation / outcome-blind held-out claim is **not verified**.
> Numerical gate checks alone do not close this gap. See
> `../experiments/tileplace_v4_timing_parser_audit_2026-09-29.json`.


当前论文材料以 VPR 9 placement 为输入基线，并用同一精确 VTR commit、seed、channel
width 和串行 router 对 refinement 前后做 route+analysis。核心入口：

- `RESULTS.md`：可直接引用的结果表、消融与边界；
- `CLAIM_MATRIX.md`：每项 claim 的证据和未完成项；
- `PAPER_DRAFT.md`：当前方法与结果正文草稿；
- `SUBMISSION_METADATA.md`：投稿系统字段、匿名设置和待确认 venue 元数据清单；
- `dac/main.tex`：可编译的 ACM/DAC 风格完整论文主文；
- `prepare_artifacts.py`：校验冻结矩阵哈希、cohort 分离和核心 claim，并从 JSON 生成
  `generated/*.tex` 表格与宏；
- `../experiments/tileplace_v4_preregistration_2026-09-03.json`：V4 routed-oracle、
  rollback/bisection 与 no-good frontier 的密封协议；
- `../experiments/tileplace_v4_development_matrix_2026-09-03.json`：四案例开发矩阵，
  CPD/WL geomean -0.804%/+0.026%；
- `../experiments/tileplace_v4_heldout/`：六案例 held-out 原始报告；
- `../experiments/tileplace_v4_heldout_matrix_2026-09-05.json`：通过全部五项 publication
  gate 的冻结主结果，CPD/WL geomean -5.049%/-0.507%，3/6 strict CPD improvements；
- `../experiments/timing_titan_stereo_extended_matrix_2026-09-02.json`：十案例、两个 architecture
  families 的 timing QoR，含五个 post-freeze validation cases 与一个 previously-probed
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
- `../experiments/titan23_stereo_vision_input_capture_2026-09-02.json`：第二个预注册 Titan23
  点的精确 Titan 2.0.0 输入、RR graph、timing、macro 与 contract provenance；
- `../experiments/titan23_stereo_vision_acquisition_2026-09-02.json`：取得完整归档前的失败尝试及
  127 个校验分块下载后的解除记录；
- `../experiments/constrained_qor_matrix_2026-09-01.json`：单独预注册的 apex4 fixed-I/O
  constrained QoR 点；28 个 fixed I/O 保持，WL/CPD +0.210%/+0.463%，不并入主 aggregate；
- `../experiments/timing_guard_ablation_2026-08-31.json`：diffeq timing 消融；
- `../experiments/page_size_ablation_2026-08-31.json`：2×2/4×4/8×8 page 消融；
- `../experiments/cpu_runtime_matrix_2026-08-31.json`：单核 CPU runtime；
- `../experiments/runtime_guard_elision_ablation_2026-08-31.json`：实现热点消融；
- `../experiments/parallel_proposal_matrix_2026-08-31.json`：并行 proposal 等价性与 scaling 边界；
- `../experiments/page_incremental_probe_2026-08-31.json`：Koios macro 与外部约束探针。

所有现有数字都是 CPU placement + VPR 原生验证，不是 FPGA 上板速度、功耗或能效。

生成论文表格并在安装 `acmart`/LaTeX 后编译：

```bash
source /inspire/hdd/global_user/guoruiyuan-253208540291/texlive/setup.sh
python3 projects/tileplace/paper/prepare_artifacts.py
make -C projects/tileplace/paper/dac
```

生成器会对 V4 held-out、十案例与 constrained 矩阵的冻结 SHA-256 fail-closed，并检查
V4 配置/预算/trial 状态链/publication gate、endpoint coverage、fixed-I/O cohort 分离和
六案例 conventional/AP 配对。当前执行主机
已用本地 TeX Live 2026、`acmart` 2.20、pdfTeX 和 BibTeX 成功生成 8 页扩展稿（7 页正文
加 1 页参考文献）；生成 PDF
仍由 `dac/.gitignore` 排除，不作为源码提交内容。
