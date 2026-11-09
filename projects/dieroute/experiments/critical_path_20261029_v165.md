# DieRoute critical path v165 — 2026-10-29

Original scope, workloads, budgets and all eight acceptance gates remain unchanged. All unchanged workstreams and retained failures remain in `experiments/critical_path_20261029_v164.md`.

Two full28,878 RTL candidates now run with the original immutable input cache and billion-cycle watchdog:

- Binary dictionary discovery: `work/resident_dictionary_binary_discovery_candidate_20261029/RTL_positive_native_monitors_v5`; xsimk679931/start1756114851.
- Direct CSR membership validation: `work/resident_CSR_membership_validation_candidate_20261029/RTL_positive_native`; xsimk1852355/start1756203622. Full original host replay plus181,568 differential checks pass; HLS estimates add2,145LUT/1,907FF/8DSP vs binary dictionary parent. Source operation reductions are not hardware speedups.

Revalidate actual handles and terminal receipts. Neither positive run has accepted full coverage. After terminal exit0, run the respective prepared `review_full_positive.py`; then execute and independently audit the observer-only negative canary. Never count configuration bootstrap as coverage, restart because logs are quiet, increase watchdog, or replace retained failures.

All platform/postroute/board and paper completion requirements remain open. Physical U280 remains unavailable; no measured speedup, energy or achieved300MHz claim.
