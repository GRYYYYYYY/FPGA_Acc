# PersistRoute paper artifact bundle

This directory freezes the evidence that can be used in a PersistRoute paper
without turning hardware emulation into a performance claim.

Generate all tables, CSV files, JSON summaries and the vector speedup figure:

```bash
python3 ../tools/prepare_paper_artifacts.py
(cd generated && sha256sum -c SHA256SUMS)
```

The generator requires successful 1-worker and 16-worker VPR records for the
ten frozen cases in `experiments/vpr9/baseline_runs`. The paired runs must have
identical route-file hashes, wirelength, CPD and iteration count; generation
fails closed on any difference.

Contents:

- `PAPER_DRAFT.md`: title, abstract, contributions, method and results prose;
- `CLAIM_MATRIX.md`: supported, partial and blocked claims;
- `EXPERIMENT_PLAN.md`: remaining measurements needed before submission;
- `generated/cpu_baseline_results.csv`: plotting/statistics source of truth;
- `generated/cpu_baseline_table.tex`: paper-ready CPU baseline table;
- `generated/cpu_baseline_speedup.svg`: vector CPU baseline figure;
- `generated/u280_resource_table.tex`: post-route U280 resource table;
- `generated/paper_results.json`: machine-readable evidence bundle;
- `generated/SHA256SUMS`: frozen artifact hashes.

The CPU speedup plot characterizes the strong VPR baseline. It is not a
PersistRoute accelerator speedup plot. Physical U280 execution is unavailable
in this VMware guest, so board runtime and energy remain deliberately absent.

## DAC manuscript

`dac/main.tex` is the anonymous ACM `acmart`/`sigconf` manuscript. It is laid
out as six pages of body text followed by one references-only page, matching
the DAC research-manuscript limit. DAC does not permit appendix material on
that seventh page, so `dac/reproducibility_appendix.tex` builds a separate
one-page artifact appendix and must not be merged into the submission PDF.

Build and enforce both page boundaries with:

```bash
cd dac
PATH=/home/gry/.local/bin:$PATH make check
```

The local build uses Tectonic 0.16.9. The manuscript intentionally retains a
visible `BOARD RESULT REQUIRED` marker: end-to-end board speedup, energy, and
ablation claims remain blocked until physical U280 measurements exist.
