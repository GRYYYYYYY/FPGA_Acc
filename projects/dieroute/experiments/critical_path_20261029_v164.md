# DieRoute critical path v164 — 2026-10-29

Original scope remains 11 workloads / 311,096 searches; all eight gates remain open. See predecessor `experiments/critical_path_20261027_v163.md` for unchanged workstreams.

- Formal 45-slot cohort is terminal: 37 final joint passes, 8 retained storage failures; five-repeat requirement remains unmet except s298 seed3.
- Original full28,878 graph RTL failed the cumulative billion-cycle fixture watchdog after one completed transaction. Separate supervisor quota failure does not establish RTL root cause.
- Binary dictionary discovery candidate passes 331 field differential cases and original full28,878 host replay with ASAN/UBSAN. HLS exits0, +420 LUT/+423 FF estimates, unchanged BRAM/URAM/DSP; no measured RTL acceleration.
- Active full28,878 candidate run: `work/resident_dictionary_binary_discovery_candidate_20261029/RTL_positive_native_monitors_v5`; xsimk679931/start1756114851 verified live. Preserve original watchdog and caches; do not restart for silence.
- On terminal, run prepared `review_full_positive.py` only after checking actual process termination. Negative observer canary remains required before candidate adoption.
- Metadata, joint, Owner and primary RTL processes remain live; postplace and platform supervisors remain queued. Revalidate handles rather than relying on this snapshot.
- Physical U280 unavailable; no board speedup, energy, achieved300MHz or platform-fit claim. Paper and acceptance gates remain incomplete.

Configuration failures and unintended dense-producer safety stop are retained in the candidate directories. Bootstrap output is configuration evidence only.
