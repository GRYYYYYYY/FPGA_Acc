# V4 reproduction audit — 2026-09-29

## Finding

The first sealed development timing pilot was rejected before any measured repetition.
The process completed successfully, but the current source did not reproduce the archived
diffeq trajectory: 1 accepted transaction instead of 5; final CPD/WL 6.59759 ns/9098
instead of 6.53077 ns/9105. The initial timing-report hash is identical, but the current
generic indexed-port parser produces 52 feedback edges instead of 37.

| Cohort | Case | Archived edges | Current parser | Restricted-port diagnostic |
|---|---|---:|---:|---:|
| development | diffeq | 37 | 52 | 37 |
| development | frisc | 30 | 43 | 30 |
| development | elliptic | 24 | 38 | 24 |
| development | clma | 96 | 124 | 96 |
| heldout | pdc | 80 | 110 | 80 |
| heldout | dsip | 31 | 61 | 31 |
| heldout | bnn | 80 | 80 | 26 |
| heldout | gemm_layer | 8 | 8 | 4 |
| heldout | tdarknet_like.small | 35 | 35 | 15 |
| heldout | ucsb_152_tap_fir | 25 | 25 | no mapped edges |

The diagnostic regex accepts only in/out/Q/D/clk indexed ports. Its summary agreement
does not prove historical source identity or full candidate equivalence. The current regex
accepts arbitrary indexed primitive ports. No parser variant was used to rerun or replace
held-out results. Only the already-seen development diffeq case was rerun.

## Evidence and consequences

- `../experiments/tileplace_v4_timing_protocol_2026-09-29.json`: pre-execution seal and source/input hashes.
- `../experiments/tileplace_v4_timing_diffeq_2026-09-29/outcome.json`: rejected pilot and both outcomes.
- `../experiments/tileplace_v4_timing_parser_audit_2026-09-29.json`: all ten initial-summary comparisons.
- `../tools/audit_v4_timing_parser.py`: read-only diagnostic; restores parser global after each case.

Archived placements, legality reports, and numerical QoR aggregates are not erased or
replaced. Their interpretation as a single frozen implementation is unresolved.
The original numeric publication gate is insufficient to establish implementation provenance.

## Next work

1. Explicitly identify and hash the parser mode, source, contract, and initial feedback in new search reports.
2. Validate one fixed implementation on a separately registered development protocol; do not select parser modes per case to recover favorable archived outcomes.
3. Treat previously observed held-out outcomes as historical evidence. They cannot become unseen data again through rerunning. Any new outcome-blind claim needs a new sealed cohort.
4. Resume paired performance measurements only after trajectory/source provenance is well defined.

## Explicit implementation identity and new development protocol

New search reports now pin the generic indexed-port parser, seven implementation
source hashes, the full contract/native inputs and exact feedback-content hashes.
They recheck source/input hashes at completion and can reject a mismatching
`--implementation-manifest` before starting search. This addresses future
provenance capture; it does not establish the missing historical source identities.

The unoptimized generic-parser baseline identity is
`dc0d7b31b411a03057597d4f215f46cfb4f29a7a2fb1a265185ca9d321996f6d`.
The new diffeq protocol targets the previously observed generic-parser trajectory,
with CPU 31, one warmup and three retained measurements. It does not target the
older restricted-parser development outcome.

A comparator amendment excludes raw artifact hashes from repeated-feedback
comparison because VPR route headers contain each run's absolute placement path.
The reports retain raw hashes for traceability; numerical feedback hashes and
parser identity remain mandatory. The completed first measured observation is
retained. The continuation seals the remaining two observations, and the combined
summary generator requires all three observations and equal complete search and
feedback identities. This amendment does not change the production algorithm.

The exact pressure-prefix optimization is subsequently sealed as
`0f8a684ae7dc745fceb257d62a71bd8f34f61bf41db5cc515dfb641b6557d2a3`.
Its completed diffeq comparison matches all candidate/decision/cost/phase and
feedback records of the generic-parser baseline. The historical mixed-parser
aggregate remains outside this equivalence claim.

## Fixed four-case development replay in progress

The sealed fixed-source protocol has completed exact repeats for diffeq,
frisc and elliptic. Frisc CPD/WL changes are -6.261%/+0.310%; elliptic changes
are -0.765%/+0.329%; diffeq remains 0.000%/-0.055%. Clma is still running,
so there is no completed four-case aggregate yet.

`tools/audit_fixed_development.py` independently checks candidate/native report
bindings, output hashes, VPR placement/routing/analysis success markers, all
repeat traces and transaction costs. `--partial` explicitly labels completed
subsets and does not establish full protocol completion. The old mixed-parser
held-out observations remain a separate historical cohort.
