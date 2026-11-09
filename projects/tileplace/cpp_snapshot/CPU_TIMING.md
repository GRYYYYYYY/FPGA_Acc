# CPU color-selection timing

Pinned to CPU 31, one warmup and five alternating measured repetitions per design. All selected transaction audits and phase statistics match exactly.

| Design | Python median (s) | C++ path median (s) | Ratio |
|---|---:|---:|---:|
| diffeq | 19.093 | 3.433 | 5.56× |
| tseng | 7.420 | 1.017 | 7.29× |
| apex2 | 13.473 | 3.991 | 3.38× |

This measures four color queries at one fixed baseline placement and feedback snapshot. C++ timing includes IPC, selected-transaction host audit and layout verification. It excludes initialization, feedback parsing, native VPR, acceptance/rollback and changing placements; it is not an end-to-end or FPGA speedup.

Full inputs, source/binary hashes and individual samples: `color_selection_benchmark_2026-09-30.json`.
