# Candidate evaluation word interface

`evaluate_words.hpp` composes the existing external-word legality, guard,
touched-network, cost-pair and Q20 score cores. It reads the same canonical
snapshot records and a caller-supplied trial. It does not enumerate candidates,
construct proposal identities, select transactions or commit a placement.

The result records before/after costs, score, negative-score acceptance, touched
count and rejection/error stage. Stages 1–5 identify legality, guards, touched
network discovery, cost and score. A rejection can have status zero; callers
must inspect stage. Failure results contain zero costs/score. The touched scratch
buffer can be written before a downstream failure; it is not committed state.
The host must validate backing capacities, canonical arrays and distinct buffers.

CPU evidence: `test_evaluate_words.cpp` checks 1,000 analytic two-block HPWL
and integer-floor cases plus stage errors. The independent HLS package at
`../work/evaluate_wire_hls_2026-09-30` freezes 15 boundary transactions and
uses a 64-bit maximum AXI width. Its monitor receipt records the actual job;
CPU checks alone do not prove RTL success or FPGA performance.

Remaining integration work includes unchanged-trial suppression, write-site
construction, candidate enumeration for move/swap/macro-swap/chain2/chain3,
full identity encoding, forbidden filtering, per-unit best selection and color
transaction selection. Existing individual word cores provide arithmetic and
legality primitives, while the validated native search still owns this control
in CPU STL containers.
