# Fixed-source no-good suppression ablation plan

Status: sealed protocol launched, exec session 25036. Implementation fed524e17a50f352ec6b6e08e12301bbf2c7df46d4b7f5a1faff71068c0a95d9; protocol SHA256 8e32b78f2078246a1ee7764e054bda5f6da8a3e35175d509e40286e531e1e7a7. All 38 tests passed before launch.

Question: under the current generic indexed-port parser, does incumbent-specific rejected-singleton suppression improve routed QoR within the same native closure budget?

Run both arms from the same source snapshot and inputs on diffeq, frisc, elliptic and clma. Enable the normal default in the treatment arm and pass --disable-no-goods in the control arm. Retain rejection tracking, stopping rules, rollback, stable bisection, feedback refresh, weights 2/2/1, guard 0, 20 timing paths, four epochs and 24 maximum closures in both arms. The switch changes only the forbidden set passed to proposal selection. Report actual calls and termination reason, since identical upper budgets do not imply equal calls.

Use two repeats per arm/case, CPU 31, sequential native VPR; preserve every trial and failure. Seal exact implementation sources, parser, runner, input hashes and commands before execution. Use new output directories. Do not reuse earlier treatment runs because the runner source identity has changed. Require repeat equality and independent native-artifact binding audits before aggregating CPD and wirelength ratios. No parameter tuning, favorable-case selection or silent failure retries. Cases are already observed development data.

The new CLI switch has a regression test in test_run_tileplace_v2.py: rejection rolls back in both arms; enabled suppression advances to an improving second candidate while disabled suppression retries the rejected candidate, under the same two-call budget. Nine controller tests pass. Historical 0f8a684a manifests remain unchanged and intentionally reject the modified runner; create a new implementation seal for this experiment.
