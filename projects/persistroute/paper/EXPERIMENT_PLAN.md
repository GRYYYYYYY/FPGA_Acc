# Submission experiment plan

## Frozen benchmark matrix

- VTR: `diffeq`, `frisc`, `elliptic`, `clma` at seed 1 and channel width 200.
- Titan23: all locally available Stratix-IV timing BLIFs, `neuron` and
  `stereo_vision`, at seed 3 and channel width 300.
- Koios 2.0: `conv_layer`, `attention_layer`, `spmv`, and `softmax`, using the
  official hard-memory include and the COFFE 22-nm complex-DSP architecture,
  at seed 1 and channel width 300.
- Commercial legality case: FPGA24 `logicnets_jscl`, compared with RWRoute,
  CUFR and Vivado using the same placed input.

## Measurements required before submission

1. Run full PersistRoute CPU golden and HBM backend on every academic case;
   report legality, wirelength, CPD, iterations, replay rate and path hashes.
2. On a physical U280, report one-time load, graph transfer, per-iteration
   Search, Commit, replay, timing snapshot, final export and total wall time.
3. Repeat board measurements at least five times after one warm-up; report
   median, dispersion and 95% confidence intervals. Keep CPU baseline runs
   isolated and pin the worker protocol.
4. Record board power over the measured region and report joules per routed
   connection and total energy, including host/device transfers.
5. Run ablations for persistent state, 1/2/4 Search CUs, MultiQueue bank count,
   transaction version checking/replay and periodic timing feedback.
6. Add pressure sweeps for channel width and congestion, plus at least three
   routing seeds where the flow is seed-sensitive.
7. Validate each final academic route with VPR and each commercial route with
   the official FPGA24 checker plus Vivado `report_route_status`/DRC.

## Current local progress

- Full per-round VPR/Tatum closure is complete for `diffeq`, `frisc`, and `elliptic`.
- One frozen four-PE HBM C-model policy uses base cost 64, three timing-aware
  reroute rounds, and deterministic criticality-first ordering. `frisc` closes
  at +0.803% CPD and `elliptic` at +0.499% versus VPR; both have zero overuse
  and byte-identical paired runs.
- The deterministic route writer now round-trips PersistRoute trees into VPR,
  and native analysis accepts `frisc` and `elliptic`. Their CPD deltas are
  +0.884%/+0.549%, while wirelength deltas are +3.656%/+3.864%; therefore the
  pre-registered 2% wirelength gate currently fails. Seven academic cases remain.
- A direct RR channel-length edge penalty was tested at `(base,length)=(64,64)`
  and `(16,16)` on `frisc`; native wirelength worsened to +4.225% and +4.632%.
  Do not tune this scalar further before testing shared-tree selection and a
  legal-route cleanup phase that preserves negotiated-congestion feasibility.

## Rejection checks

- If full end-to-end speedup over the strong multicore baseline is below 3x,
  narrow the claim to an architecture/transaction study or retarget FCCM/FPL.
- If mean wirelength or CPD degradation exceeds 2%, fix the routing/timing
  policy before performance tuning.
- If persistent-state and transaction ablations do not explain the speedup,
  the current novelty claim is not isolated.
- If the commercial flow cannot emit a complete legal route, do not use the
  commercial-case result as an end-to-end routing claim.
