# Frozen VPR baseline feasibility

The executable is VPR `9.0.0-dev+8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07`, SHA-256 `a90dc1b3380ebda705e85f176db0cc3d6be1b71ab9ee887db819febc8b62bafc`. The binary's own `--help` is retained in `evidence/vpr_help_excerpt.txt`; the full input identity is in `source_manifest.json`.

The frozen source registers `--read_initial_place_file` in `vpr/src/base/read_options.cpp:1636`. In `vpr/src/place/initial_placement.cpp:1190`, that branch reads the supplied placement instead of generating an initial placement, then loads movable blocks and checks legality. `vpr/src/place/placer.cpp:107` initializes costs and subsequently constructs a fresh `PlacementAnnealer`. This is executable **placement-seeded reannealing**, not a checkpoint continuation of temperature, move history, RNG, timing state or native route trees. It is more specific than an unrelated random restart. The [official VPR CLI documentation](https://docs.verilogtorouting.org/en/latest/vpr/command_line_usage/#cmdoption-read_initial_place_file) agrees with this placement-start semantics; the local frozen source and binary are the authority for this test.

The single frozen smoke uses diffeq, seed 1, channel width 200, CPU31, one worker, the same architecture/BLIF/packed netlist and initial placement as TP, and explicit `--place_algorithm criticality_timing --timing_analysis on --place --route --analysis`. It does not change inner_num, initial temperature, stopping rules, or try another seed based on the result. Default auto schedule and router remain unchanged. Any contract VPR floorplan constraints are forwarded. Neither pipeline supplies a separate SDC file; each runs in a fresh directory and uses VPR's default timing constraints for these inputs. The native command, logs, full process timer and final consistency checks are archived. Timeout is 900 seconds, with no retry.

| Comparator | Meaning | Role |
|---|---|---|
| B0 | Existing legal placement/routing | Common start only; zero extra search |
| B1 | Same placement seeds fresh native timing-driven SA, then route/analysis | Strong executable baseline candidate; smoke is not equal-budget efficacy |
| B2 | Same TP controller, generic parser, edge-walk pressure sum | Mechanism ablation |
| A | Same TP controller, sparse pressure-prefix | Existing exact scoring optimization |

The historical wirelength-oriented AP result is supplementary. DREAMPlaceFPGA/AMF input alignment remains unresolved; neither toolchain is rebuilt here. A completed B1 run establishes a callable route to a fair timing-driven comparator, not universal fairness or a TP win. Its native objective and TP's timing-first acceptance rule differ internally; final CPD/WL admissibility is evaluated against the common start. A formal budget protocol would still need fixed wall budgets, the same admissibility rule, and fully checked outputs before cutoff.

The one frozen smoke completed with exit 0 and all native placement/routing consistency checks. Outer time: **2.017749213 s**; native VPR: **1.699172121 s**; remaining input preparation/check/write/startup: **0.318577092 s**. Output CPD **6.61216 ns**, WL **9097**, legal **true**. The common start has CPD **6.59759 ns**, WL **9103**; TP has the same CPD and WL **9098**. The smoke candidate fails the common timing-first acceptance rule (`timing_first_acceptance_not_met`); preserve B0 as incumbent. This is an executable baseline, not evidence of a win at equal QoR or equal total budget.

Evidence: `evidence/pilot/diffeq_baseline_smoke/{command.json,native_command.json,process.json,report.json,native_excerpt.txt}`. Exact hashes and local raw-log/output paths are in the native report. No second seed, alternate temperature schedule, retry, or AP replacement was attempted. The wall-budget search/selection loop remains unimplemented in this round; it must select only fully validated outputs before cutoff.
