#!/usr/bin/env python3
"""Acquire a BLIF TilePlace case, endpoint contract, and native baseline closure."""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, sha256


SUCCESS = (
    "Completed placement consistency check successfully.",
    "Completed routing consistency check successfully.",
    "Circuit successfully routed with a channel width factor",
    "VPR succeeded",
)


def checked(path: Path) -> Path:
    result = path.resolve()
    if not result.is_file():
        raise ContractError(f"missing input: {result}")
    return result


def run(command: list[str], cwd: Path, stdout: Path, stderr: Path, env=None) -> float:
    start = time.monotonic()
    process = subprocess.run(command, cwd=cwd, env=env, text=True, capture_output=True, check=False)
    stdout.write_text(process.stdout)
    stderr.write_text(process.stderr)
    if process.returncode != 0:
        raise ContractError(f"command exited with {process.returncode}: {' '.join(command)}")
    return time.monotonic() - start


def metric(pattern: str, text: str, label: str, cast):
    match = re.search(pattern, text, re.MULTILINE)
    if not match:
        raise ContractError(f"baseline log is missing {label}")
    return cast(match.group(1))


def command_stage(command: list[str], cwd: Path, name: str, env=None) -> dict:
    stdout, stderr = cwd / f"{name}.stdout.log", cwd / f"{name}.stderr.log"
    wall = run(command, cwd, stdout, stderr, env)
    return {
        "command": command,
        "wall_s": wall,
        "stdout": {"path": str(stdout), "sha256": sha256(stdout)},
        "stderr": {"path": str(stderr), "sha256": sha256(stderr)},
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case", required=True)
    parser.add_argument("--vpr", type=Path, required=True)
    parser.add_argument("--timing-vpr", type=Path, required=True)
    parser.add_argument("--architecture", type=Path, required=True)
    parser.add_argument("--circuit", type=Path, required=True)
    parser.add_argument("--sdc", type=Path)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--channel-width", type=int, required=True)
    parser.add_argument("--max-router-iterations", type=int)
    parser.add_argument(
        "--rebuild-timing-rr-graph",
        action="store_true",
        help="Rebuild the deterministic RR graph in recovery stages instead of deserializing --read_rr_graph",
    )
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        if args.seed < 0 or args.channel_width <= 0:
            raise ContractError("invalid seed or channel width")
        vpr, timing_vpr = checked(args.vpr), checked(args.timing_vpr)
        architecture, circuit = checked(args.architecture), checked(args.circuit)
        sdc = checked(args.sdc) if args.sdc else None
        root = args.work.resolve()
        root.mkdir(parents=True, exist_ok=True)
        baseline = root / "baseline"
        baseline.mkdir(exist_ok=True)
        net, place, route = baseline / "baseline.net", baseline / "baseline.place", baseline / "baseline.route"
        rr_graph = baseline / "rr_graph.xml"
        baseline_stdout, baseline_stderr = baseline / "vpr.stdout.log", baseline / "vpr.stderr.log"
        if not all(path.is_file() for path in (net, place, route, rr_graph, baseline_stdout)):
            if any(baseline.iterdir()):
                raise ContractError("partial baseline directory exists; preserve it and inspect before retry")
            command = [
                str(vpr), str(architecture), str(circuit),
                "--net_file", str(net), "--place_file", str(place), "--route_file", str(route),
                "--write_rr_graph", str(rr_graph), "--seed", str(args.seed), "--num_workers", "1",
                "--route_chan_width", str(args.channel_width), "--echo_file", "on",
            ]
            if sdc:
                command.extend(["--sdc_file", str(sdc)])
            if args.max_router_iterations is not None:
                command.extend(["--max_router_iterations", str(args.max_router_iterations)])
            command.extend(["--pack", "--place", "--route", "--analysis"])
            wall = run(command, baseline, baseline_stdout, baseline_stderr)
            (baseline / "command.json").write_text(json.dumps({"command": command, "wall_s": wall}, indent=2) + "\n")
        baseline_text = baseline_stdout.read_text() + baseline_stderr.read_text()
        if not all(marker in baseline_text for marker in SUCCESS):
            raise ContractError("baseline VPR success markers are incomplete")
        for path in (net, place, route, rr_graph):
            checked(path)
        baseline_metrics = {
            "wirelength": metric(r"Total wirelength:\s+(\d+)", baseline_text, "wirelength", int),
            "cpd_ns": metric(
                r"Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns",
                baseline_text, "CPD", float,
            ),
            "routing_iterations": metric(
                r"Successfully routed after (\d+) routing iterations", baseline_text, "iterations", int
            ),
        }

        connections = root / "connections.csv"
        if not connections.is_file():
            command_stage(
                [sys.executable, str(Path(__file__).parents[2] / "persistroute/tools/vpr_route_connections.py"),
                 str(route), str(connections)], root, "connections"
            )
        timing_input = root / "reference_timing.input.csv"
        timing_input_report = root / "reference_timing.input.json"
        if not timing_input.is_file():
            command_stage(
                [sys.executable, str(Path(__file__).with_name("prepare_reference_timing_input.py")),
                 "--connections", str(connections), "--output", str(timing_input),
                 "--report", str(timing_input_report)], root, "timing_input"
            )
        timing_output = root / "reference_timing.output.csv"
        if not timing_output.is_file():
            env = os.environ.copy()
            env.update(
                {
                    "PERSISTROUTE_VPR_BIN": str(timing_vpr),
                    "PERSISTROUTE_VPR_ARCH": str(architecture),
                    "PERSISTROUTE_VPR_CIRCUIT": str(circuit),
                    "PERSISTROUTE_VPR_NET": str(net),
                    "PERSISTROUTE_VPR_PLACE": str(place),
                    "PERSISTROUTE_VPR_ROUTE": str(route),
                    "PERSISTROUTE_VPR_CHAN_WIDTH": str(args.channel_width),
                }
            )
            if not args.rebuild_timing_rr_graph:
                env["PERSISTROUTE_VPR_RR_GRAPH"] = str(rr_graph)
            if sdc:
                env["PERSISTROUTE_VPR_SDC"] = str(sdc)
            command_stage(
                [sys.executable, str(Path(__file__).parents[2] / "persistroute/tools/vpr_timing_analyzer.py"),
                 str(0xFFFFFFFF), str(timing_input), str(timing_output)], root, "timing_export", env
            )

        macros = root / "vpr_place_macros.echo"
        macro_report = root / "vpr_macro_capture.json"
        if not macros.is_file():
            command = [
                sys.executable, str(Path(__file__).with_name("capture_vpr_macros.py")),
                "--vpr", str(vpr), "--architecture", str(architecture), "--circuit", str(circuit),
                "--netlist", str(net), "--place", str(place),
                "--work", str(root / "macro_work"), "--output", str(macros), "--report", str(macro_report),
                "--seed", str(args.seed), "--channel-width", str(args.channel_width),
            ]
            if not args.rebuild_timing_rr_graph:
                command.extend(["--rr-graph", str(rr_graph)])
            else:
                command.extend(["--source-echo", str(baseline / "place_macros.echo")])
            if sdc:
                command.extend(["--", "--sdc_file", str(sdc)])
            command_stage(command, root, "macro_capture")

        contract = args.contract.resolve()
        if not (contract / "manifest.json").is_file():
            command_stage(
                [
                    sys.executable, str(Path(__file__).with_name("tileplace_vpr.py")), "pack",
                    "--netlist", str(net), "--place", str(place), "--rr-graph", str(rr_graph),
                    "--architecture", str(architecture), "--native-macros", str(macros),
                    "--connections", str(connections), "--timing", str(timing_output),
                    "--output", str(contract),
                    "--vpr-revision", "8cb20aa5293b5ce5f6a05c88b37b38e1305d9b07",
                    "--seed", str(args.seed), "--channel-width", str(args.channel_width),
                    "--vpr-command", f"vpr {architecture.name} {circuit.name} --seed {args.seed} --num_workers 1 --route_chan_width {args.channel_width}",
                ], root, "contract_pack"
            )

        closure_report = root / "vpr_native_closure.json"
        if not closure_report.is_file():
            command = [
                sys.executable, str(Path(__file__).with_name("run_vpr_closure.py")),
                "--contract", str(contract), "--vpr", str(vpr), "--architecture", str(architecture),
                "--circuit", str(circuit), "--netlist", str(net), "--golden-place", str(place),
                "--work", str(root / "closure_work"), "--report", str(closure_report),
                "--seed", str(args.seed), "--channel-width", str(args.channel_width),
            ]
            if args.max_router_iterations is not None:
                command.extend(["--max-router-iterations", str(args.max_router_iterations)])
            if not args.rebuild_timing_rr_graph:
                command.extend(["--", "--read_rr_graph", str(rr_graph)])
            if sdc:
                command.extend(["--sdc_file", str(sdc)])
            command_stage(command, root, "native_closure")
        closure = json.loads(closure_report.read_text())

        with timing_output.open(newline="") as stream:
            timing_rows = list(csv.DictReader(stream))
        report = {
            "schema": "TILEPLACE_BLIF_CASE_ACQUISITION_V1",
            "status": "pass",
            "case": args.case,
            "seed": args.seed,
            "channel_width": args.channel_width,
            "inputs": {
                "vpr": {"path": str(vpr), "sha256": sha256(vpr)},
                "timing_vpr": {"path": str(timing_vpr), "sha256": sha256(timing_vpr)},
                "architecture": {"path": str(architecture), "sha256": sha256(architecture)},
                "circuit": {"path": str(circuit), "sha256": sha256(circuit)},
                **({"sdc": {"path": str(sdc), "sha256": sha256(sdc)}} if sdc else {}),
            },
            "baseline_flow": baseline_metrics,
            "native_baseline_closure": {
                "wirelength": closure["wirelength"], "cpd_ns": closure["cpd_ns"],
                "legal": closure["legal"], "report": {"path": str(closure_report), "sha256": sha256(closure_report)},
            },
            "artifacts": {
                "netlist": {"path": str(net), "sha256": sha256(net)},
                "place": {"path": str(place), "sha256": sha256(place)},
                "route": {"path": str(route), "sha256": sha256(route)},
                "rr_graph": {"path": str(rr_graph), "sha256": sha256(rr_graph)},
                "connections": {"path": str(connections), "sha256": sha256(connections)},
                "timing": {"path": str(timing_output), "sha256": sha256(timing_output), "rows": len(timing_rows)},
                "macros": {"path": str(macros), "sha256": sha256(macros)},
                "contract_manifest": {"path": str(contract / "manifest.json"), "sha256": sha256(contract / "manifest.json")},
            },
        }
        dump_json(args.report.resolve(), report)
        print(json.dumps({"case": args.case, **baseline_metrics, "timing_rows": len(timing_rows)}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError, csv.Error) as error:
        print(f"prepare_tileplace_blif_case: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
