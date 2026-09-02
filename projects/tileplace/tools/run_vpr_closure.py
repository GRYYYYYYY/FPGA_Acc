#!/usr/bin/env python3
"""Run a fail-closed VPR route/analysis check on a TilePlace golden placement."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

from tileplace_vpr import ContractError, validate_contract


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def absolute(path: Path) -> Path:
    path = path.resolve()
    if not path.is_file():
        raise ContractError(f"required file does not exist: {path}")
    return path


def match(pattern: str, text: str, label: str, cast: type = str):
    result = re.search(pattern, text, re.MULTILINE)
    if not result:
        raise ContractError(f"VPR log is missing {label}")
    return cast(result.group(1))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--vpr", type=Path, required=True)
    parser.add_argument("--architecture", type=Path, required=True)
    parser.add_argument("--circuit", type=Path, required=True)
    parser.add_argument("--netlist", type=Path, required=True)
    parser.add_argument("--golden-place", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--channel-width", type=int, required=True)
    parser.add_argument("--max-router-iterations", type=int)
    parser.add_argument("extra_vpr_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    extra_vpr_args = args.extra_vpr_args[1:] if args.extra_vpr_args[:1] == ["--"] else args.extra_vpr_args

    try:
        contract = args.contract.resolve()
        vpr = absolute(args.vpr)
        architecture = absolute(args.architecture)
        circuit = absolute(args.circuit)
        netlist = absolute(args.netlist)
        golden_place = absolute(args.golden_place)
        manifest = json.loads((contract / "manifest.json").read_text())
        netlist_before = sha256(netlist)
        golden_before = sha256(golden_place)
        if netlist_before != manifest["inputs"]["packed_netlist"]["sha256"]:
            raise ContractError("packed netlist does not match the contract manifest")
        architecture_hash = sha256(architecture)
        circuit_hash = sha256(circuit)
        if manifest["packed_netlist"].get("architecture_id") != f"SHA256:{architecture_hash}":
            raise ContractError("architecture does not match the packed-netlist architecture id")
        if manifest["packed_netlist"].get("atom_netlist_id") != f"SHA256:{circuit_hash}":
            raise ContractError("circuit does not match the packed-netlist atom-netlist id")
        if args.seed != manifest["vpr"]["seed"] or args.channel_width != manifest["vpr"]["channel_width"]:
            raise ContractError("seed/channel width do not match the contract manifest")
        validate_contract(contract, golden_place)

        work = args.work.resolve()
        work.mkdir(parents=True, exist_ok=True)
        vpr_netlist = work / "vpr_input.net"
        post_routing_netlist = work / "vpr_input.net.post_routing"
        vpr_place = work / "vpr_input.place"
        route = work / "vpr_output.route"
        native_macros = work / "place_macros.echo"
        stdout_path = work / "vpr.stdout.log"
        stderr_path = work / "vpr.stderr.log"
        shutil.copyfile(netlist, vpr_netlist)
        shutil.copyfile(golden_place, vpr_place)
        command = [
            str(vpr),
            str(architecture),
            str(circuit),
            "--net_file",
            str(vpr_netlist),
            "--place_file",
            str(vpr_place),
            "--route_file",
            str(route),
            "--seed",
            str(args.seed),
            "--num_workers",
            "1",
            "--route_chan_width",
            str(args.channel_width),
            "--echo_file",
            "on",
        ]
        if "vpr_constraints" in manifest.get("inputs", {}):
            constraint_path = Path(manifest["inputs"]["vpr_constraints"]["path"])
            if not constraint_path.is_file():
                raise ContractError(f"VPR constraints input does not exist: {constraint_path}")
            if sha256(constraint_path) != manifest["inputs"]["vpr_constraints"]["sha256"]:
                raise ContractError("VPR constraints input hash does not match the contract manifest")
            command.extend(["--read_vpr_constraints", str(constraint_path)])
        if args.max_router_iterations is not None:
            command.extend(["--max_router_iterations", str(args.max_router_iterations)])
        command.extend(extra_vpr_args)
        command.extend(["--route", "--analysis"])
        start = time.monotonic()
        process = subprocess.run(command, cwd=work, text=True, capture_output=True, check=False)
        wall_s = time.monotonic() - start
        stdout_path.write_text(process.stdout)
        stderr_path.write_text(process.stderr)
        combined = process.stdout + process.stderr
        if process.returncode != 0:
            raise ContractError(f"VPR exited with status {process.returncode}; see {stdout_path}")
        for marker in (
            "Completed placement consistency check successfully.",
            "Completed routing consistency check successfully.",
            "Circuit successfully routed with a channel width factor",
            "VPR succeeded",
        ):
            if marker not in combined:
                raise ContractError(f"VPR success marker is missing: {marker}")
        if not route.is_file():
            raise ContractError("VPR did not create the requested route file")
        if not post_routing_netlist.is_file():
            raise ContractError("VPR did not create the post-routing packed netlist")
        if not native_macros.is_file():
            raise ContractError("VPR did not create place_macros.echo")
        if sha256(native_macros) != manifest["inputs"]["native_macros"]["sha256"]:
            raise ContractError("VPR regenerated placement macros differ from the contract input")
        native_validation = validate_contract(contract, vpr_place)
        if sha256(netlist) != netlist_before:
            raise ContractError("VPR modified the archived packed netlist")
        if sha256(golden_place) != golden_before:
            raise ContractError("VPR modified the archived CPU golden placement")

        vpr_version = match(r"^Version:\s+(.+)$", combined, "VPR version")
        vpr_revision = match(r"^Revision:\s+(.+)$", combined, "VPR revision")
        expected_revision = manifest["vpr"]["revision"]
        expected_hash = expected_revision.rsplit("g", 1)[-1]
        if not vpr_revision.startswith(expected_hash):
            raise ContractError(
                f"VPR revision {vpr_revision!r} does not match contract revision {expected_revision!r}"
            )

        report = {
            "schema": "TILEPLACE_VPR_NATIVE_CLOSURE_V1",
            "status": "pass",
            "legal": True,
            "command": command,
            "returncode": process.returncode,
            "wall_s": wall_s,
            "seed": args.seed,
            "channel_width": args.channel_width,
            "max_router_iterations": args.max_router_iterations,
            "routing_iterations": match(r"Successfully routed after (\d+) routing iterations", combined, "iteration count", int),
            "wirelength": match(r"Total wirelength:\s+(\d+)", combined, "wirelength", int),
            "cpd_ns": match(r"Final critical path delay \(least slack\):\s+([0-9.]+) ns", combined, "CPD", float),
            "max_rss_mib": match(r"entire flow .*\(max_rss ([0-9.]+) MiB\)", combined, "peak RSS", float),
            "vpr_version": vpr_version,
            "vpr_revision": vpr_revision,
            "inputs": {
                "vpr": {"path": str(vpr), "sha256": sha256(vpr)},
                "architecture": {"path": str(architecture), "sha256": architecture_hash},
                "circuit": {"path": str(circuit), "sha256": circuit_hash},
                "netlist": {"path": str(netlist), "sha256": netlist_before},
                "golden_place": {"path": str(golden_place), "sha256": golden_before},
            },
            "outputs": {
                "vpr_netlist_copy": {"path": str(vpr_netlist), "sha256": sha256(vpr_netlist)},
                "post_routing_netlist": {"path": str(post_routing_netlist), "sha256": sha256(post_routing_netlist)},
                "vpr_place_copy": {"path": str(vpr_place), "sha256": sha256(vpr_place)},
                "route": {"path": str(route), "sha256": sha256(route)},
                "native_macros": {"path": str(native_macros), "sha256": sha256(native_macros)},
                "stdout": {"path": str(stdout_path), "sha256": sha256(stdout_path)},
                "stderr": {"path": str(stderr_path), "sha256": sha256(stderr_path)},
            },
            "placement_validation": native_validation,
        }
        args.report.resolve().parent.mkdir(parents=True, exist_ok=True)
        args.report.resolve().write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"run_vpr_closure: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
