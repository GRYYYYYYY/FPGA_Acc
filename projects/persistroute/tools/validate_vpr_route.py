#!/usr/bin/env python3
"""Run VPR's native route reader/checker and summarize legality and QoR."""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
from pathlib import Path


PLACEMENT_ID = re.compile(r"^Placement_File:\s+\S+\s+Placement_ID:\s+SHA256:([0-9a-f]{64})$")
WIRELENGTH = re.compile(r"Total wirelength:\s+(\d+)")
CPD = re.compile(r"Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def parse_vpr_output(stdout: str):
    wire = WIRELENGTH.findall(stdout)
    cpd = CPD.findall(stdout)
    markers = {
        "route_loaded": "Finished loading route file" in stdout,
        "routing_consistency": "Completed routing consistency check successfully." in stdout,
        "successfully_routed": "Circuit successfully routed" in stdout,
        "vpr_succeeded": "VPR succeeded" in stdout,
    }
    return markers, (int(wire[-1]) if wire else None), (float(cpd[-1]) if cpd else None)


def validate(args):
    route_header = args.route.read_text(encoding="utf-8", errors="replace").splitlines()[0]
    match = PLACEMENT_ID.match(route_header)
    if not match:
        raise ValueError("route header lacks a SHA256 Placement_ID")
    place_sha = sha256(args.place)
    if match.group(1) != place_sha:
        raise ValueError(f"route Placement_ID {match.group(1)} differs from place SHA256 {place_sha}")

    args.work_dir.mkdir(parents=True, exist_ok=True)
    local_net = args.work_dir / args.net.name
    local_place = args.work_dir / args.place.name
    local_route = args.work_dir / args.route.name
    shutil.copy2(args.net, local_net)
    shutil.copy2(args.place, local_place)
    shutil.copy2(args.route, local_route)
    command = [
        str(args.vpr.resolve()), str(args.arch.resolve()), str(args.circuit.resolve()),
        "--analysis", "--net_file", local_net.name, "--place_file", local_place.name,
        "--route_file", local_route.name, "--route_chan_width", str(args.channel_width),
        "--read_rr_graph", str(args.rr_graph.resolve()),
    ]
    completed = subprocess.run(command, cwd=args.work_dir, text=True, capture_output=True)
    stdout_path = args.work_dir / "vpr_analysis.stdout"
    stderr_path = args.work_dir / "vpr_analysis.stderr"
    stdout_path.write_text(completed.stdout, encoding="utf-8")
    stderr_path.write_text(completed.stderr, encoding="utf-8")
    markers, wirelength, cpd_ns = parse_vpr_output(completed.stdout)
    legal = completed.returncode == 0 and all(markers.values()) and wirelength is not None and cpd_ns is not None
    result = {
        "schema": "PERSISTROUTE_VPR_NATIVE_VALIDATION_V1",
        "legal": legal,
        "vpr_exit_status": completed.returncode,
        **markers,
        "channel_width": args.channel_width,
        "total_wirelength": wirelength,
        "critical_path_delay_ns": cpd_ns,
        "baseline_wirelength": args.baseline_wirelength,
        "wirelength_delta_percent": (
            100.0 * (wirelength / args.baseline_wirelength - 1.0)
            if wirelength is not None and args.baseline_wirelength else None
        ),
        "baseline_cpd_ns": args.baseline_cpd_ns,
        "cpd_delta_percent": (
            100.0 * (cpd_ns / args.baseline_cpd_ns - 1.0)
            if cpd_ns is not None and args.baseline_cpd_ns else None
        ),
        "inputs": {
            "vpr_sha256": sha256(args.vpr), "arch_sha256": sha256(args.arch),
            "circuit_sha256": sha256(args.circuit), "net_sha256": sha256(args.net),
            "place_sha256": place_sha, "route_sha256": sha256(args.route),
            "rr_graph_sha256": sha256(args.rr_graph),
        },
        "stdout_sha256": sha256(stdout_path),
        "stderr_sha256": sha256(stderr_path),
        "command": command,
    }
    report = args.report or args.work_dir / "validation.json"
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    if not legal:
        raise RuntimeError(f"VPR native validation failed; see {stdout_path} and {stderr_path}")
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--vpr", required=True, type=Path)
    parser.add_argument("--arch", required=True, type=Path)
    parser.add_argument("--circuit", required=True, type=Path)
    parser.add_argument("--net", required=True, type=Path)
    parser.add_argument("--place", required=True, type=Path)
    parser.add_argument("--route", required=True, type=Path)
    parser.add_argument("--rr-graph", required=True, type=Path)
    parser.add_argument("--channel-width", required=True, type=int)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    parser.add_argument("--baseline-wirelength", type=int)
    parser.add_argument("--baseline-cpd-ns", type=float)
    args = parser.parse_args()
    print(json.dumps(validate(args), indent=2))


if __name__ == "__main__":
    main()
