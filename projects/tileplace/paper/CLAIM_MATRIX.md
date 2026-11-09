# TilePlace claim matrix

> **2026-09-29 provenance audit:** A full diffeq timing replay does not reproduce
> the archived V4 trajectory. With the same hashed timing report, the current
> port parser yields 52 initial edges instead of 37. Four development summaries
> plus pdc/dsip disagree with the current parser and match a diagnostic
> restricted-port variant. Archived QoR values remain intact, but the
> single-frozen-implementation / outcome-blind held-out claim is **not verified**.
> Numerical gate checks alone do not close this gap. See
> `../experiments/tileplace_v4_timing_parser_audit_2026-09-29.json`.


| Claim | Current evidence | Status | Remaining work |
|---|---|---|---|
| Prospective source-sealed local cohort | 13 completed cases, 9 successful paired evaluations, 404 audited native trials, two exact trajectories per success; successful-subset CPD/WL -1.944%/-0.213%, 7/9 strict CPD improvements | Supported for the nine successful local logic-oriented cases; four failures retained | Strict historical blindness, heterogeneous architecture generalization and broader end-to-end coverage remain unproven |
| Input-chain end-to-end coverage | 9/13 completed; adder architecture mismatch; ex1010/s298/s38417 native baselines legal but CPU input generator retains 8/2/2 overused resources after 30 iterations | Measured limitation; no retries | Separate future protocol for input-chain improvements; do not silently repair or pool this frozen cohort |
| Fixed-source no-good suppression contribution | Four paired designs, two repeats per arm, 272 native trials; CPD change 0%, WL geomean -0.013735%; diffeq calls 8→16 | No CPD benefit demonstrated in this cohort | Broader preregistered mechanism validation before attributing timing gains to suppression |
| Current fixed-source development reproducibility | Four cases, 10 exact repetitions, 176 audited native trials; CPD/WL geomeans -1.825%/+0.168% | Proven on observed development cases | New preregistered validation for generalization; historical parser provenance remains unresolved |
| Real VPR legality and heterogeneity | Five-case correctness matrix; 2866 blocks; Koios CLB/DSP/memory/IO and 43 macros | Proven | None for CPU correctness |
| Native region/fixed constraints | Two official VTR XML cases and fail-closed recovery; separate post-freeze apex4 point preserves 28 coordinate-fixed I/O and closes natively, with retained +0.210% WL/+0.463% CPD | Proven for legality and one separately reported QoR point | Add a constrained suite before making aggregate constrained-QoR claims |
| Deterministic page transactions | 1/2/4/8 fork workers exactly match serial on four cases; disjoint site/net commit; macro atomicity | Proven on current cases | C++/shared-snapshot implementation for actual scaling |
| Native routed-oracle acceptance and exact rollback | All six V4 held-out outputs are native legal; every trial archives candidate placement, native closure, decision, and reason; matrix audit verifies final state chains and closure budgets | Proven for the preregistered cohort | Broader preregistered replication |
| No-good frontier escapes repeated oracle-bad proxy optima | V3 repeatedly stopped at one rejected proxy frontier; V4 development CPD geomean is -0.804% with 3/4 strict improvements, and held-out tdarknet reaches a later -21.289% CPD incumbent | Archived observations; controlled source-consistent ablation unverified | Repeat frontier ablation under one sealed implementation |
| V4 held-out timing improvement | Six-case CPD/WL geomeans -5.049%/-0.507%; 3/6 strict CPD improvements; worst WL +0.270%; all five preregistered publication clauses pass | Numerically supported by archived runs; single-implementation provenance unresolved | Broader architectures and held-out designs before superiority claims |
| Connection-specific timing is necessary | Net-level and unguarded connection-star diffeq ablation both regress CPD | Proven on diffeq | Broader timing-model ablation |
| Critical-distance guard controls timing risk | Diffeq CPD regression removed; ten-case/two-architecture-family CPD geomean -0.911%, worst +0.017%; all five post-freeze cases and the macro-stress case are non-regressing | Supported | Pre-register tolerance on a broader suite |
| Routed wirelength improves | Ten-case geomean -0.066%, worst +0.439%; post-freeze quintet geomean +0.015%; Titan23 neuron/stereo are retained at +0.088%/+0.135%; macro-stress conv_layer -0.124% | Supported only in aggregate, and small | Broader matrix; congestion-aware cost |
| Better than executable VPR cluster-level AP | Same packed netlist/router on the original six-case subset; AP is +3.711% WL/+16.103% CPD geomean while TilePlace is -0.071%/-0.300% vs conventional SA | Proven for this experimental six-case VPR AP path | Do not generalize to attention_layer or external timing-driven placers |
| Better than independent placers | DREAMPlaceFPGA `0044943...` and AMF-Placer `70d9828...` source/CLI audits are archived as B1 candidates, but both change the netlist/architecture/backend methodology | Not supported | Use a separately pre-registered Bookshelf/FPGAIF/Vivado cohort; do not merge it into the same-packed-netlist VPR matrix |
| Endpoint timing coverage | Main ten cases: 280205/280205 clustered and 275654 atom mapped, with 4551 explicit unmapped rows; separate apex4 constrained point maps 2263/2263 at both levels | Proven with explicit distinction | Extend constrained timing coverage beyond one point |
| Earlier guarded-reference CPU runtime | Six-case medians 0.545--59.672 s; full samples and variability archived; spmv/softmax CV 2.8%/2.2% | Measured for the earlier reference only; excludes V4 oracle calls | Add controlled V4 end-to-end timing and equal-time comparisons |
| CPU parallel speedup | Controlled clma 1/2/4/8 process results show no speedup | Not supported | Replace Python IPC with C++ or HLS dataflow |
| Full-color hardware correctness | October 4 frozen full-color baseline: five/four RTL transactions with 150/120 complete typed-port comparisons; native differential cohort: nine cases, 202 trials, 88 color calls, 129 unique input identities | Supported for that baseline and those fixtures; see COMPLETION_GATES.md for receipts | Optimized candidates require their own complete validation; broader benchmark RTL coverage remains distinct from native coverage |
| Internal 4 ns hardware timing | Clocked October 9 baseline WNS -0.660 ns; roots shift-end candidate WNS -0.237 ns with 918 setup failures; eligible implementation pending | Timing closure not achieved | A single final candidate must satisfy both correctness and routed setup/hold/pulse/route/DRC gates |
| FPGA acceleration | A full-color external-word implementation now exists beyond the original toy kernel, but no physical U280 performance is measured | Not supported | Complete final implementation validation and platform integration; physical measurements are required for board runtime, speedup, power or energy claims |

## Current generic-parser implementation optimization

| Claim | Evidence | Scope | Remaining work |
|---|---|---|---|
| Indexed congestion pressure preserves exact edge-walk cost | Independent sparse-grid walk comparison, both L orders and feedback refreshes; full diffeq phase/transaction-cost/decision/placement/feedback equality | Proven for regression cases and one current development trajectory | Four-case current replay completed; broader paired equivalence remains pending |
| Pressure-prefix CPU improvement | One warmup/three measured samples per version on CPU 31; full-process 88.741→69.044 s (1.285×), proposal 66.768→47.724 s (1.399×) | Single-case diagnostic; shared host, sequential measurements | Broader paired development suite and interleaved measurement |

These rows do not resolve the historical mixed-parser provenance gap and do not
support FPGA acceleration or external-placer superiority.
