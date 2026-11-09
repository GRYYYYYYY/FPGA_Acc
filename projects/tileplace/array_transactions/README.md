# Array transaction selection

This separate directory preserves the source identity of the running nine-design ArrayShapeSearch batch.

`selection.hpp` sorts record indices by score and host-supplied full-identity rank, then checks conflicts against previously selected site/net/unit CSR ranges. The data plane allocates no containers. It validates capacities and ranges before touching caller scratch or outputs. Unique identity ranks and canonical unit IDs must be supplied by a host encoder; full identity encoding and search integration remain pending.

One thousand transaction sets (sizes 0–64, score ties, nonnegative scores and site/net/unit conflicts) match the existing select_transactions reference, including selection order. Two invalid range/capacity cases preserve both buffers. The independent CMake/CTest check passes 1/1. This is CPU semantic evidence, not HLS synthesis or acceleration.

Build with `cmake -S projects/tileplace/array_transactions -B /tmp/tileplace-array-transactions-build`, then build and run CTest there.

`identity.hpp` now compares the full kind byte string, nested unit-member sequences and sorted trial block/coordinate sequences without containers. Five thousand comparisons over 500 identities match the original proposal tuple ordering, including string prefixes and equality. Referenced arrays must be validated before calling. It is not yet wired into transaction selection; the independent CTest suite passes 2/2.

`identity_selection.hpp` now sorts directly by score and complete identity arrays, removing the host-rank requirement. It validates conflict CSR ranges, identity kind/unit/trial ranges, all nested member ranges and capacities before any buffer write. One thousand transaction sets match reference selected identities and order; six malformed-range/capacity cases preserve buffers. Independent CTest passes 3/3. Canonical identity ordering and unit conflict IDs still require an encoder, and live search integration remains pending.

`encoder.hpp` now encodes real Proposal objects into kind/unit/trial identity arrays and site/net/unit conflict CSR records, normalizing outer unit order as the original selector does. A per-batch unit dictionary preserves full macro-unit identity. One thousand sets verify identity roundtrips and selected identity/score/net/site equivalence, including two-member macro units and reversed outer-unit order. Independent CTest passes 4/4. Encoding uses host containers; selection remains array-only. Live candidate integration remains pending and can be added here without changing the running batch.

`TransactionArraySearch` now uses the encoded full-identity array selector at the end of color candidate generation. Sixty guarded unit sets, 48 guarded colors and 144 resident adapter calls match Python; independent CTest passes 5/5. Host encoding/control still use containers. Diffeq native validation is running under `../work/transaction_array_native_diffeq_2026-09-30`; native completion is not yet established.

The new fast transaction service returns eligible/proposal/accepted/conflict/kind statistics. `FastTransactionEngine` audits only selected transactions. Across 144 calls in 12 constrained fixtures, identities/scores and all phase statistics match Python before/after commit, feedback and restore. A patched Python full-enumeration method raises on invocation during every fast call, confirming it is not used. CPU candidate control and host encoding still use STL; fast native closure validation remains pending.

The checked transaction-array diffeq native pilot completed: 16 closures/16 color calls, independently audited exact complete trajectory and final placement. Receipt: `../work/transaction_array_native_diffeq_2026-09-30/differential_audit.json`. The selected-only fast version is now running native diffeq under `../work/fast_transaction_native_diffeq_2026-09-30`; its result is pending.

Fast native diffeq completed and independent audit passes: 16 closures/16 color calls, exact complete search/feedback signatures, phases, transactions and final placement, with selected-only Python audits and C++ phase statistics. Receipt: `../work/fast_transaction_native_diffeq_2026-09-30/differential_audit.json`. No CPU acceleration or hardware claim follows from this equivalence run.
