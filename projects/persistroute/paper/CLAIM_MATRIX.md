# PersistRoute claim matrix

| Proposed claim | Status | Local evidence | Paper wording boundary |
|---|---|---|---|
| Production graph/task ABI supports real VPR RR graphs | Supported | converter tests; `experiments/vpr9_*`; 32-byte `Task` audit | State exact tested graph sizes and hashes. |
| Connection-level speculative search plus deterministic commit reaches legal PathFinder closure | Supported in CPU/HBM C-model | `vpr9_baseline_suite_2026-08-24.json`; timing-criticality experiment | Do not generalize the tested closures to every Titan/Koios case. |
| Four Search CUs and one Commit CU implement the intended transaction protocol | Supported in RTL emulation | `accelerated_pathfinder_hw_emu_2026-08-26.json` | Claim functional equivalence, not performance. |
| Per-connection VPR/Tatum criticality is refreshed and deterministically reprioritizes the next routing round | Supported in CPU/HBM C-model | `timing_criticality_2026-08-26.json`; `timing_priority_{frisc,elliptic}_2026-08-27.json` | The timing-mode RTL subset has not been rerun. |
| Full U280 design closes timing at 180 MHz | Supported | `vitis_link_2022_2_u280.json` | Quote WNS/TNS/WHS/THS and post-synthesis dynamic-region resources. |
| VPR 1-worker/16-worker baseline is deterministic over ten frozen cases | Supported after artifact generation | `paper/generated/paper_results.json` | Describe it as CPU baseline characterization. |
| PersistRoute preserves wirelength/CPD within 2% on the full benchmark matrix | Partial | One frozen timing-priority policy gives `frisc` +0.803% and `elliptic` +0.499% CPD; both are deterministic | Two-design CPD evidence is not a matrix result; VPR route export/validation and all remaining cases are required. |
| PersistRoute is at least 3x faster than a strong multicore router end to end | Blocked | no physical U280 in the VM | Never use `hw_emu` wall time. Requires board execution including transfer, timing update and export. |
| PersistRoute reduces energy | Blocked | no board power trace | Requires repeatable board power/energy measurement. |
| Results are statistically stable | Partial | deterministic paired routes exist, but formal repeated board runs do not | Add repeated runs, confidence intervals and multi-seed sensitivity where applicable. |

The defensible novelty is the combination of persistent cross-iteration RR
state, version-checked deterministic transactions and two-level hardware
parallelism. Deterministic parallel routing, connection-aware parallelism,
MultiQueue search, overlap tolerance and HBM use each have prior art and must
not be claimed independently as firsts.
