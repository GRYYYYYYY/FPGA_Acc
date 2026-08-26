#!/usr/bin/env python3
"""Run a PersistRoute-enabled VPR/Tatum analysis for one routing iteration.

The patched VPR loads the original legal route only to initialize the clustered
timing graph.  Before Tatum STA it replaces every routed connection delay with
the delay supplied by the current PersistRoute paths, then exports raw setup
criticality and slack for every connection.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path


REQUIRED = (
    "PERSISTROUTE_VPR_BIN",
    "PERSISTROUTE_VPR_ARCH",
    "PERSISTROUTE_VPR_CIRCUIT",
    "PERSISTROUTE_VPR_NET",
    "PERSISTROUTE_VPR_PLACE",
    "PERSISTROUTE_VPR_ROUTE",
    "PERSISTROUTE_VPR_CHAN_WIDTH",
)


def main() -> int:
    if len(sys.argv) != 4:
        print("usage: vpr_timing_analyzer.py <iteration> <input.csv> <output.csv>", file=sys.stderr)
        return 2
    missing = [name for name in REQUIRED if not os.environ.get(name)]
    if missing:
        raise SystemExit("missing VPR timing environment: " + ", ".join(missing))
    iteration = int(sys.argv[1], 10)
    timing_input = Path(sys.argv[2]).resolve()
    timing_output = Path(sys.argv[3]).resolve()
    if not timing_input.is_file():
        raise SystemExit(f"timing input does not exist: {timing_input}")

    paths = {name: Path(os.environ[name]).resolve() for name in REQUIRED[:-1]}
    for name, path in paths.items():
        if not path.is_file():
            raise SystemExit(f"{name} does not exist: {path}")
    channel_width = int(os.environ["PERSISTROUTE_VPR_CHAN_WIDTH"], 10)
    if channel_width <= 0:
        raise SystemExit("PERSISTROUTE_VPR_CHAN_WIDTH must be positive")

    timing_output.parent.mkdir(parents=True, exist_ok=True)
    timing_output.unlink(missing_ok=True)
    with tempfile.TemporaryDirectory(prefix=f"persistroute_vpr_timing_{iteration:03d}_") as work_text:
        work = Path(work_text)
        net = work / paths["PERSISTROUTE_VPR_NET"].name
        place = work / paths["PERSISTROUTE_VPR_PLACE"].name
        route = work / paths["PERSISTROUTE_VPR_ROUTE"].name
        for source, target in ((paths["PERSISTROUTE_VPR_NET"], net),
                               (paths["PERSISTROUTE_VPR_PLACE"], place),
                               (paths["PERSISTROUTE_VPR_ROUTE"], route)):
            target.symlink_to(source)
        log = Path(str(timing_output) + ".vpr.log")
        env = os.environ.copy()
        env["PERSISTROUTE_VPR_TIMING_INPUT"] = str(timing_input)
        env["PERSISTROUTE_VPR_TIMING_OUTPUT"] = str(timing_output)
        command = [
            str(paths["PERSISTROUTE_VPR_BIN"]),
            str(paths["PERSISTROUTE_VPR_ARCH"]),
            str(paths["PERSISTROUTE_VPR_CIRCUIT"]),
            "--analysis",
            "--net_file", net.name,
            "--place_file", place.name,
            "--route_file", route.name,
            "--route_chan_width", str(channel_width),
            "--timing_report_npaths", "1",
        ]
        sdc_text = os.environ.get("PERSISTROUTE_VPR_SDC")
        if sdc_text:
            sdc_source = Path(sdc_text).resolve()
            if not sdc_source.is_file():
                raise SystemExit(f"PERSISTROUTE_VPR_SDC does not exist: {sdc_source}")
            sdc = work / sdc_source.name
            sdc.symlink_to(sdc_source)
            command.extend(("--sdc_file", sdc.name))
        with log.open("w", encoding="utf-8") as stream:
            completed = subprocess.run(command, cwd=work, env=env, stdout=stream,
                                       stderr=subprocess.STDOUT, check=False)
        if completed.returncode != 0:
            print(f"VPR timing analysis failed (exit {completed.returncode}); see {log}", file=sys.stderr)
            return completed.returncode
    if not timing_output.is_file():
        print("patched VPR did not create timing output; apply vpr_timing_export.patch", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
