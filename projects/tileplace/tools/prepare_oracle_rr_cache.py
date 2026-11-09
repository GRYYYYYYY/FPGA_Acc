#!/usr/bin/env python3
"""Build equivalent binary RR-graph and router-lookahead caches for native closures."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from tileplace_vpr import ContractError, sha256


def checked(path: Path) -> Path:
    path = path.resolve()
    if not path.is_file():
        raise ContractError(f"missing input: {path}")
    return path


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vpr", type=Path, required=True)
    parser.add_argument("--architecture", type=Path, required=True)
    parser.add_argument("--circuit", type=Path, required=True)
    parser.add_argument("--netlist", type=Path, required=True)
    parser.add_argument("--place", type=Path, required=True)
    parser.add_argument("--route", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--channel-width", type=int, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--rr-cache", type=Path, required=True)
    parser.add_argument("--lookahead-cache", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        vpr, architecture, circuit = checked(args.vpr), checked(args.architecture), checked(args.circuit)
        netlist, place, route = checked(args.netlist), checked(args.place), checked(args.route)
        if args.seed < 0 or args.channel_width <= 0:
            raise ContractError("invalid seed or channel width")
        inputs = {path: sha256(path) for path in (netlist, place, route)}
        work = args.work.resolve()
        work.mkdir(parents=True, exist_ok=True)
        private_net, private_place, private_route = (
            work / netlist.name, work / place.name, work / route.name
        )
        for source, target in (
            (netlist, private_net), (place, private_place), (route, private_route)
        ):
            shutil.copyfile(source, target)
        rr_cache = args.rr_cache.resolve()
        lookahead = args.lookahead_cache.resolve()
        rr_cache.parent.mkdir(parents=True, exist_ok=True)
        lookahead.parent.mkdir(parents=True, exist_ok=True)
        command = [
            str(vpr), str(architecture), str(circuit), "--analysis",
            "--net_file", str(private_net), "--place_file", str(private_place),
            "--route_file", str(private_route), "--seed", str(args.seed),
            "--num_workers", "1", "--route_chan_width", str(args.channel_width),
            "--write_rr_graph", str(rr_cache),
            "--write_router_lookahead", str(lookahead),
        ]
        start = time.monotonic()
        process = subprocess.run(command, cwd=work, text=True, capture_output=True, check=False)
        wall = time.monotonic() - start
        stdout, stderr = work / "vpr.stdout.log", work / "vpr.stderr.log"
        stdout.write_text(process.stdout)
        stderr.write_text(process.stderr)
        if process.returncode != 0:
            raise ContractError(f"VPR exited with {process.returncode}; see {stdout}")
        for marker in (
            "Completed placement consistency check successfully.",
            "Completed routing consistency check successfully.",
            "VPR succeeded",
        ):
            if marker not in process.stdout + process.stderr:
                raise ContractError(f"VPR success marker is missing: {marker}")
        for output in (rr_cache, lookahead):
            checked(output)
        if any(sha256(path) != digest for path, digest in inputs.items()):
            raise ContractError("source netlist/place/route changed during cache generation")
        report = {
            "schema": "TILEPLACE_ORACLE_RR_CACHE_V1",
            "status": "pass",
            "seed": args.seed,
            "channel_width": args.channel_width,
            "wall_s": wall,
            "command": command,
            "inputs": {
                "vpr": {"path": str(vpr), "sha256": sha256(vpr)},
                "architecture": {"path": str(architecture), "sha256": sha256(architecture)},
                "circuit": {"path": str(circuit), "sha256": sha256(circuit)},
                "netlist": {"path": str(netlist), "sha256": inputs[netlist]},
                "place": {"path": str(place), "sha256": inputs[place]},
                "route": {"path": str(route), "sha256": inputs[route]},
            },
            "outputs": {
                "rr_cache": {"path": str(rr_cache), "sha256": sha256(rr_cache), "bytes": rr_cache.stat().st_size},
                "lookahead_cache": {"path": str(lookahead), "sha256": sha256(lookahead), "bytes": lookahead.stat().st_size},
                "stdout": {"path": str(stdout), "sha256": sha256(stdout)},
                "stderr": {"path": str(stderr), "sha256": sha256(stderr)},
            },
        }
        report_path = args.report.resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": "pass", "wall_s": wall, "rr_bytes": rr_cache.stat().st_size,
                          "lookahead_bytes": lookahead.stat().st_size}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError) as error:
        print(f"prepare_oracle_rr_cache: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
