# Cost diagnostics and accounting boundaries

R0/R1 performance processes have no observation AST or profiler. Correctness runs add full enumeration digests and full-key distinct sets; cProfile is enabled only for the first proposal. Its self times partition that instrumented call graph; cumulative times overlap and **must not be added**. They do not estimate uninstrumented full-workload shares. Full exclusive flow stages are in cost_breakdown.csv; rejected oracle work is nested in oracle_driver. The old proposal fraction is never treated as eliminable cache time.

| First-proposal diagnostic | Function | Calls | Self s | Cumulative s (nested) |
|---|---|---:|---:|---:|
| diffeq/R0 | propose_color | 1 | 0.001814 | 16.348717 |
| diffeq/R0 | _transactions_for_unit | 11 | 0.059577 | 16.264839 |
| diffeq/R0 | _make_transaction | 3149 | 0.082798 | 12.793870 |
| diffeq/R0 | _cost_pair | 3138 | 0.938416 | 10.264442 |
| diffeq/R0 | _connection_congestion | 647231 | 0.606748 | 5.063818 |
| diffeq/R0 | _valid_trial | 3149 | 0.047974 | 1.055442 |
| diffeq/R0 | _guard_ok | 3138 | 0.010791 | 0.047738 |
| diffeq/R1 | propose_color | 1 | 0.001975 | 11.782174 |
| diffeq/R1 | _transactions_for_unit | 11 | 0.060455 | 11.695915 |
| diffeq/R1 | _make_transaction | 3149 | 0.085261 | 8.156284 |
| diffeq/R1 | _cost_pair | 3138 | 0.869652 | 5.595723 |
| diffeq/R1 | _connection_congestion | 8920 | 0.010574 | 0.092911 |
| diffeq/R1 | _valid_trial | 3149 | 0.049406 | 1.074694 |
| diffeq/R1 | _guard_ok | 3138 | 0.011207 | 0.049759 |
| diffeq/R1 | get | 647231 | 0.851974 | 1.163368 |
| clma/R0 | propose_color | 1 | 0.033168 | 94.903558 |
| clma/R0 | _transactions_for_unit | 38 | 0.291549 | 93.523940 |
| clma/R0 | _make_transaction | 12492 | 0.411780 | 78.768583 |
| clma/R0 | _cost_pair | 12454 | 6.603581 | 67.922593 |
| clma/R0 | _connection_congestion | 3542335 | 3.360559 | 28.779272 |
| clma/R0 | _valid_trial | 12492 | 0.200004 | 4.298990 |
| clma/R0 | _guard_ok | 12454 | 0.081352 | 0.232926 |
| clma/R1 | propose_color | 1 | 0.033859 | 69.656820 |
| clma/R1 | _transactions_for_unit | 38 | 0.292415 | 68.228181 |
| clma/R1 | _make_transaction | 12492 | 0.415408 | 53.152590 |
| clma/R1 | _cost_pair | 12454 | 6.150871 | 42.142760 |
| clma/R1 | _connection_congestion | 108178 | 0.125829 | 1.126578 |
| clma/R1 | _valid_trial | 12492 | 0.204233 | 4.392840 |
| clma/R1 | _guard_ok | 12454 | 0.079034 | 0.236555 |
| clma/R1 | get | 3542335 | 4.675695 | 7.409896 |

The reference scalar's return depends only on pressure version and ordered endpoint x/y. Actual full-flow query distributions are in reuse_profile.csv, split into before/candidate roles and pressure epochs. Apply/restore boundaries are counted by observer_event_map.json/observations.json; they leave the scalar memo intact. Terminal cleanup calls reset once, so invalidation counters include initial allocation and final release and must not be read as accepted-feedback counts. R0 performance does not maintain diagnostic unique-key sets: zero fields there mean not observed, not zero real calls.

The first clma performance pair illustrates why proposal is not synonymous with cacheable work: R0 proposal 216.660198 s versus R1 146.267515 s, while oracle_driver is 145.348668 / 151.386766 s and feedback 18.230635 / 18.485561 s. Full times are 386.208064 / 321.977825 s. Variation in the necessary native part is retained, not subtracted to inflate benefit. Both measured pairs, including all rejected trials, remain in runtime_samples.csv.

## Aggregate operation diagnostic

Fresh initial real endpoint inputs (diffeq 1973 pairs, clma first 2048 pairs), actual initial route pressure, 20000 iterations per main loop. These are aggregate wall times including loop/dispatch cost; do not subtract loop_control as an exact overhead correction. memo_cold_fill uses one pass of the pair list, eviction uses 2000 operations, and clear empties 131072 entries. Construction/lookup rows isolate operations, while the full memo-hit row includes key construction, counters and return. Rows intentionally overlap conceptually; do not sum them. This separate diagnostic costs 2.623688 s outer, with pressure/input preparation included. It is not a workload speedup or a substitute for complete timers.

| Case | Operation | Aggregate seconds |
|---|---|---:|
| diffeq | loop_control | 0.001608195 |
| diffeq | key_construct | 0.004551641 |
| diffeq | dictionary_lookup | 0.002820914 |
| diffeq | prefix_scalar_compute | 0.060821055 |
| diffeq | position_dict_copy | 0.015429961 |
| diffeq | memo_cold_fill | 0.005883466 |
| diffeq | memo_hit_path_including_key_counters_return | 0.015319893 |
| diffeq | fifo_2000_evictions | 0.001282957 |
| diffeq | clear_131072_entries | 0.000744152 |
| clma | loop_control | 0.001662075 |
| clma | key_construct | 0.005019824 |
| clma | dictionary_lookup | 0.002612453 |
| clma | prefix_scalar_compute | 0.066015874 |
| clma | position_dict_copy | 0.096488709 |
| clma | memo_cold_fill | 0.008188628 |
| clma | memo_hit_path_including_key_counters_return | 0.015695407 |
| clma | fifo_2000_evictions | 0.001162629 |
| clma | clear_131072_entries | 0.000631785 |

Position copies, candidate generation, guards and filtering/sorting/conflict selection are unchanged. Copies are measured separately by the aggregate diagnostic; their exact exclusive full-workload share is not inferred from that microbenchmark. In cProfile, generation/selection residuals appear in _transactions_for_unit/propose_color self time, and copy/normalization bookkeeping in _make_transaction self time. All are charged by the actual performance outer timer.

All runs start with empty memo tables; no free prefill. The hard entry bound is 131072 FIFO entries, hit queries do not reorder it, and misses recompute using unchanged prefix arithmetic. The synthetic reduced-capacity test exercises 2124 evictions; the actual clma workload exercises 478. Cache build/fill, misses, invalidation and final release are included. Peak RSS is process-self HWM, not a process-tree peak or an allocator-exact measurement of cache bytes.

TP time-quality timestamps are recorded after native closure and feedback handling. For the budget table, outer-minus-entry residual is conservatively added to every timestamp, so startup is not free; this also includes a small tail cost. These are upper bounds from the performance runs, not a separate paired efficacy experiment. Native loops use an outer monotonic start including initialization, netlist copying, all fresh-SA/route/analysis/check/hash work. Post-cutoff candidates are never admitted. Raw legal rejected points remain in quality_points.csv.

Cold deployment remains unknown. Historical preparation is not added to new times. The finite results do not prove unseen-design behavior, board performance, or novel dependency reuse.
