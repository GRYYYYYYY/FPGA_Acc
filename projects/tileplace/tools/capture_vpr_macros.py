#!/usr/bin/env python3
"""Capture VPR-native placement macros from frozen architecture/netlist inputs."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from tileplace_vpr import ContractError, parse_place, parse_vpr_place_macros, sha256


def absolute(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ContractError(f"required file does not exist: {resolved}")
    return resolved


def root_attributes(path: Path) -> dict[str, str]:
    for _event, element in ET.iterparse(path, events=("start",)):
        return dict(element.attrib)
    raise ContractError(f"{path}: empty packed netlist")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vpr", type=Path, required=True)
    parser.add_argument("--architecture", type=Path, required=True)
    parser.add_argument("--circuit", type=Path, required=True)
    parser.add_argument("--netlist", type=Path, required=True)
    parser.add_argument("--place", type=Path, required=True)
    parser.add_argument("--rr-graph", type=Path)
    parser.add_argument(
        "--source-echo",
        type=Path,
        help="Reuse a place_macros.echo emitted by the frozen baseline VPR run",
    )
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--channel-width", type=int, required=True)
    parser.add_argument("extra_vpr_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    extra_vpr_args = (
        args.extra_vpr_args[1:]
        if args.extra_vpr_args[:1] == ["--"]
        else args.extra_vpr_args
    )

    try:
        vpr = absolute(args.vpr)
        architecture = absolute(args.architecture)
        circuit = absolute(args.circuit)
        netlist = absolute(args.netlist)
        place = absolute(args.place)
        rr_graph = absolute(args.rr_graph) if args.rr_graph else None
        attrs = root_attributes(netlist)
        if attrs.get("architecture_id") != f"SHA256:{sha256(architecture)}":
            raise ContractError("architecture does not match the packed-netlist architecture id")
        if attrs.get("atom_netlist_id") != f"SHA256:{sha256(circuit)}":
            raise ContractError("circuit does not match the packed-netlist atom-netlist id")

        if args.source_echo:
            source_echo = absolute(args.source_echo)
            _header, rows = parse_place(place)
            placements = {row["name"]: row for row in rows}
            _macros, summary = parse_vpr_place_macros(source_echo, placements)
            output = args.output.resolve()
            output.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source_echo, output)
            report = {
                "schema": "TILEPLACE_VPR_MACRO_CAPTURE_V1",
                "status": "pass",
                "mode": "reuse_frozen_baseline_echo",
                "seed": args.seed,
                "channel_width": args.channel_width,
                "placement_consistency": "inherited_from_frozen_baseline_vpr",
                "macros": summary,
                "inputs": {
                    "vpr": {"path": str(vpr), "sha256": sha256(vpr)},
                    "architecture": {"path": str(architecture), "sha256": sha256(architecture)},
                    "circuit": {"path": str(circuit), "sha256": sha256(circuit)},
                    "netlist": {"path": str(netlist), "sha256": sha256(netlist)},
                    "place": {"path": str(place), "sha256": sha256(place)},
                    "source_echo": {"path": str(source_echo), "sha256": sha256(source_echo)},
                },
                "output": {"path": str(output), "sha256": sha256(output)},
            }
            report_path = args.report.resolve()
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
            print(json.dumps({"status": "pass", **summary, "sha256": sha256(output)}, sort_keys=True))
            return 0

        work = args.work.resolve()
        work.mkdir(parents=True, exist_ok=True)
        work_netlist = work / "vpr_input.net"
        work_place = work / "vpr_input.place"
        route = work / "vpr_output.route"
        stdout = work / "vpr.stdout.log"
        stderr = work / "vpr.stderr.log"
        echo = work / "place_macros.echo"
        shutil.copyfile(netlist, work_netlist)
        shutil.copyfile(place, work_place)
        command = [
            str(vpr),
            str(architecture),
            str(circuit),
            "--net_file",
            str(work_netlist),
            "--place_file",
            str(work_place),
            "--route_file",
            str(route),
            "--seed",
            str(args.seed),
            "--num_workers",
            "1",
            "--route_chan_width",
            str(args.channel_width),
            "--max_router_iterations",
            "1",
            "--echo_file",
            "on",
        ]
        if rr_graph is not None:
            command.extend(["--read_rr_graph", str(rr_graph)])
        command.extend(extra_vpr_args)
        command.append("--route")
        start = time.monotonic()
        process = subprocess.run(command, cwd=work, text=True, capture_output=True, check=False)
        wall_s = time.monotonic() - start
        stdout.write_text(process.stdout)
        stderr.write_text(process.stderr)
        combined = process.stdout + process.stderr
        if "Completed placement consistency check successfully." not in combined:
            raise ContractError("VPR did not pass native placement consistency")
        if process.returncode != 0 and not all(
            marker in combined
            for marker in (
                "Circuit is unroutable with a channel width factor",
                "VPR failed to implement circuit",
            )
        ):
            raise ContractError(f"VPR exited unexpectedly with status {process.returncode}")
        if not echo.is_file():
            raise ContractError("VPR did not create place_macros.echo")
        revision_match = re.search(r"^Revision:\s+(.+)$", combined, re.MULTILINE)
        if not revision_match:
            raise ContractError("VPR log is missing its revision")

        _header, rows = parse_place(place)
        placements = {row["name"]: row for row in rows}
        _macros, summary = parse_vpr_place_macros(echo, placements)
        output = args.output.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(echo, output)
        report = {
            "schema": "TILEPLACE_VPR_MACRO_CAPTURE_V1",
            "status": "pass",
            "command": command,
            "vpr_returncode": process.returncode,
            "vpr_revision": revision_match.group(1),
            "wall_s": wall_s,
            "seed": args.seed,
            "channel_width": args.channel_width,
            "routing_iteration_limit": 1,
            "placement_consistency": "pass",
            "macros": summary,
            "inputs": {
                "vpr": {"path": str(vpr), "sha256": sha256(vpr)},
                "architecture": {"path": str(architecture), "sha256": sha256(architecture)},
                "circuit": {"path": str(circuit), "sha256": sha256(circuit)},
                "netlist": {"path": str(netlist), "sha256": sha256(netlist)},
                "place": {"path": str(place), "sha256": sha256(place)},
            },
            "output": {"path": str(output), "sha256": sha256(output)},
            "logs": {
                "stdout": {"path": str(stdout), "sha256": sha256(stdout)},
                "stderr": {"path": str(stderr), "sha256": sha256(stderr)},
            },
        }
        if rr_graph is not None:
            report["inputs"]["rr_graph"] = {"path": str(rr_graph), "sha256": sha256(rr_graph)}
        report_path = args.report.resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": "pass", **summary, "sha256": sha256(output)}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError, ET.ParseError) as error:
        print(f"capture_vpr_macros: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
