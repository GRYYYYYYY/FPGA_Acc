# Paper-level strong baselines

The runner records hashes, exact commands, host information, tool-version logs,
stdout/stderr, exit status, full wall time and (when GNU time is available) peak
RSS. `B0` means a locally auditable
run; `B1` requires a local CLI/version audit; `B2` is literature-only and is
intentionally not executable.

```powershell
python run_strong_baselines.py --baseline vpr_parallel --cases cases.json --output runs
python run_strong_baselines.py --baseline vpr_parallel --cases cases.json --case case_id --output runs
python run_strong_baselines.py --baseline rwroute --cases cases.json --output runs
python run_strong_baselines.py --baseline vivado_route --cases cases.json --output runs
python parse_qor.py runs\...\stdout.log runs\...\timing_summary.rpt --output metrics.json
```

Use fixed channel width and seed for paired VPR routing comparisons. Use the
same placed DCP for PersistRoute, RWRoute, CUFR and Vivado routing comparisons.
Vivado reports are the final commercial legality and timing reference.

Official interfaces: [VPR command line](https://docs.verilogtorouting.org/en/latest/vpr/command_line_usage/),
[RWRoute invocation](https://www.rapidwright.io/docs/Implementation_Basics.html), and
[Vivado route status](https://docs.amd.com/r/en-US/ug835-vivado-tcl-commands/report_route_status).
