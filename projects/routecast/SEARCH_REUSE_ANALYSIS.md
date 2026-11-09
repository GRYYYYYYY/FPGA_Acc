# RouteCast: NET-local search reuse

This note records the reasoning behind the isolated `tools/net_shared_capacity_forecast.py` experiment. It does not certify native routability, predict failure accurately, or prove total pipeline acceleration.

## Fixed demand during a NET

Let L(v) be the ledger counting distinct NET owners of node v, and U(v) the indicator of ownership by the active NET. Search reads O(v)=L(v)-U(v). A committed connection adds one to both L and U exactly on nodes newly acquired by this NET; elsewhere neither changes. Thus O is invariant throughout its contiguous connection group. At the start of that group U is empty, so copying the current ledger once suffices. This depends on processing each NET only once and on there being no external ledger mutation between queries.

Consequently capacities, destination demand multipliers and RC edge costs remain fixed across the group. All connections must share the same SOURCE. A change of placement, endpoints, RC model, other-NET ledger or history invalidates the reused state. No cache across updates is implemented here.

## Why a shared shortest-path tree is a candidate replacement

With nonnegative edge costs, fixed adjacency ordering, heap ordering `(cost,node)` and strict-less label replacement, a settled node's selected predecessor is stable. Restarting this deterministic search from the same SOURCE reproduces the settled prefix. A predecessor on a previously returned sink path was selected in that prefix. Incoming edges removed by the original NET-parent constraint did not win that node's label in the unrestricted prefix; removing those alternatives should therefore preserve that prefix and the subsequent canonical search tree. This is an algorithmic argument to be checked against implementation semantics, not a machine-checked theorem.

The original loop stops before relaxing the target. The shared loop relaxes it and retains the frontier for the next query. For physical terminal SINK nodes there are no outgoing arcs, so this difference is inert. Arbitrary nonterminal targets and zero-cost ties have additional synthetic coverage, but no universal equivalence claim follows from random tests. Negative RC increments invalidate Dijkstra; the current isolated module does not add a production input validator for this condition.

## Evidence and limitations

Nine physical mux cases retain exact paths, RC delays, demand costs, ledger and query commits for 9993 connections. Search expansion events deliberately differ. All frozen original predictions had independent physical/XML audits; semantic identity transfers that bounded result to these candidates. It also transfers the same pressure errors and false overuse, rather than improving accuracy.

A deterministic 1000-graph probe covers positive edges and terminal targets in both capacity modes. A separate 10000-graph probe permits zero-cost edges and outgoing target arcs. Their 2000 and 20000 comparisons respectively find no mismatch; small synthetic graphs do not establish scalability or full physical hard-mode equivalence.

A fresh largest-case ABBA block is stored under `experiments/mux_NET_shared_ABBA_2026-10-06`. Its final receipt and independent verification, when complete, are authoritative for timing. Setup, output serialization, native routing and acceptance are outside those search times. One block is insufficient for statistical confidence or cross-family performance generalization.

## Adoption gates

Before using this as a production replacement: validate source consistency, NET grouping, nonnegative costs and cache invalidation; preserve incomplete-query status and commit semantics; audit full physical hard-capacity cohorts; measure complete update cost against native-only routing; and evaluate pressure accuracy independently. Concurrent or durable publication remains the responsibility of the broader RouteCast state design and is not supplied by this optimization.
