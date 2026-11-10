# Method distinction and exact dependencies

Evidence base: `2019e8fc5bb410cb2a4b1d9bb5f557dc5682b08e`; original source base remains `b32afa4303a5574dde7171b4ae6e3d07aeb8a06c`. Only phase2_B is new. R0 imports the frozen phase2_A source; R1 overrides only `_connection_congestion`. Both use prefix-on and the original generic parser, candidate/controller rules and native closure. The effective implementation identity is the reference source **plus** entry.py/reuse.py, not the old seven-file hash alone.

For ordered endpoints a,b and immutable pressure snapshot P, the cached value is min(cost of horizontal-then-vertical L, cost of vertical-then-horizontal L). Each path cost is Manhattan length times 65536 plus the exact integer sum of pressure weights. The actual read set is P, ax, ay, bx, by. Key `(snapshot_version, ax, ay, bx, by)` is sufficient; no endpoint-order symmetry is assumed. A fresh monotone version and empty table follow every pressure setter, including rollback to a prior snapshot. The bound is 131072 entries, deterministic FIFO eviction, with exact computation on every miss. Apply/restore alone do not invalidate this scalar cache. It stores Python arbitrary-precision integers; no precision change or new division is introduced.

| Mechanism | Stored/recomputed value | Relevant dependencies | Distinction |
|---|---|---|---|
| Existing prefix | Sparse pressure sums | Pressure snapshot | Fast evaluation of one L path; present in all arms |
| Existing net-cache | Before aggregate for a net | Current placement and pressure; cleared by apply/restore | Does not supply each changed-connection contribution |
| Existing touched-net delta | Candidate versus incumbent totals | Net membership/extrema, moved endpoints, criticalities, routed timing | Already incremental; not a new contribution |
| R1 | Exact congestion scalar for complete arguments | Ordered endpoint x/y and pressure version | Ordinary memoization across before/candidate queries; no extra dependence mechanism |
| Proposed R2 | No additional implemented value | Same fixed-feedback scalar read set | Not implemented: no ability beyond fair R1 has been identified |
| VPR update_td_costs | Incremental timing connection/net costs | Changed criticality and current delay | Direct overlap with general incremental-contribution rationale |

VPR source inspected at frozen VTR `8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07`, `vpr/src/place/place_timing_update.cpp`: update_td_costs (around 256) updates modified-criticality connections and consistently sums nets; commit_setup_slacks (194) and verify_connection_setup_slacks (220) retain commit/verification distinctions. This is a narrow direct-overlap check, not an exhaustive novelty survey.

Whole transaction scores are deliberately not cached. Nonmoving net members affect HPWL; criticality and routed-feedback changes affect separate terms; Q20 normalization uses before totals and integer floor division. Guard, legality, no-good, tie-breaking, conflict selection and native acceptance remain unchanged. Endpoint equality never implies route/STA equality. Every submitted candidate still receives native verification, including rejected trials.

The full-flow observer is separate from performance mode: it instruments decision/return and scoring boundaries of the frozen reference AST, hashes fixed 4096-record chunks, and retains nonzero stage counts and small examples. Independent R0/R1 runs compare these plus native signatures. This is empirical equivalence of recorded events, not a formal proof for arbitrary inputs. The original synthetic cost vectors cover invalidation/overflow/HPWL/timing/restore. A separately preregistered synthetic legal-site enumerator additionally compares 1237 move/swap/macro_swap/chain2/chain3 attempts and 24 batches, including guard/no-good/restore and numerical stale-key witnesses. This is not a claim of native macro coverage beyond what the two real designs actually enumerate.

Correctness runs are the sole warmups and carry full-key uniqueness bookkeeping, summaries, and cProfile on **the first proposal only**. First-proposal profiling cannot be scaled into a complete-run exclusive cost partition. Observation cost is included in the resource ledger and excluded from performance ratios. Full run timers retain startup, all rejection/rollback/native/feedback/write costs. Cold-deployment remains unknown.
