# Evidence map

`history/cohort/` contains the original 13-case summary, final audit and all 18 successful repeat reports/timers. `history/failures/` retains the four input failures. `history/preparation/` preserves the exact preparation commands, return codes and timers. `historical_trial_index.csv` has all 404 original native trial receipts, copied under `history/native/`. These are trials, not independent designs or new experiments.

`history/supporting/` keeps generic-parser and prefix timing, fixed-development, rollback repair and negative frontier-ablation records separately. These have distinct implementation identities and must not be merged with the 13-case main table. Historical Git source commits are unknown; implementation fingerprints are available. The old V4 parser audit is deliberately retained: for the same diffeq timing-report SHA, the old summary has 37 edges while the generic parser has 52. Historical six-case −5.049% is excluded from the current unified-source table.

`pilot/` contains new bounded-run receipts and derived summaries after completion. `trial_index.csv` points to each new native receipt. Large candidate placement/route/netlist/graph data remain local; `local_artifacts.csv` and the source/input manifest record their paths, sizes and SHA provenance. A SHA in a historical native receipt is not silently presented as a fresh rehash; the accepted phase1 verification is reused.

`cold_accounting.csv` records historical component accounting, not a new observed cold-deployment experiment. `hardware_gate.csv` is an independent historical timing gate only. It is not system runtime or board evidence.

The top-level `evidence_index.csv` lists compact packaged bytes, SHA, original paths and derivation status. `source_manifest.json` binds the new isolated implementation, generic parser, Python/taskset/VPR, runner, adapter and directly consumed inputs. No benchmark corpus, tool binary, FPGA binary, waveform or license-restricted raw data is packaged.

Portable summary check from a repository clone: `python3 DAC_AUDIT/phase2_A/verify_compact.py`. This uses only the packaged small JSON/CSV/source files. Native replication and the separate `validate_delivery.py` raw-artifact checks require the original server inputs and runtime output directory.
