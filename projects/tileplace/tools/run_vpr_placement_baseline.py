#!/usr/bin/env python3
"""Run an auditable same-packed-netlist VPR placement/route baseline."""

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

from tileplace_vpr import ContractError, parse_place, validate_contract


AP_OPTION = "--enable_analytic_placer"
AP_START_MARKER = "Creating analytic placement for"
AP_TIMER_MARKER = "Analytic Placement took"


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def absolute_file(path: Path) -> Path:
    result = path.resolve()
    if not result.is_file():
        raise ContractError(f"required file does not exist: {result}")
    return result


def match(pattern: str, text: str, label: str, cast: type = str):
    result = re.search(pattern, text, re.MULTILINE)
    if not result:
        raise ContractError(f"VPR log is missing {label}")
    return cast(result.group(1))


def optional_match(pattern: str, text: str, cast: type = float):
    result = re.search(pattern, text, re.MULTILINE)
    return None if not result else cast(result.group(1))


def parse_vpr_metrics(text: str) -> dict[str, object]:
    return {
        "routing_iterations": match(
            r"Successfully routed after (\d+) routing iterations", text, "routing iteration count", int
        ),
        "wirelength": match(r"Total wirelength:\s+(\d+)", text, "routed wirelength", int),
        "cpd_ns": match(
            r"Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns", text, "CPD", float
        ),
        "max_rss_mib": match(
            r"The entire flow of VPR took .*\(max_rss ([0-9.]+) MiB\)", text, "peak RSS", float
        ),
        "stage_times_s": {
            "initial_placement": optional_match(r"^## Initial Placement took ([0-9.]+) seconds", text),
            "placement": optional_match(r"^# Placement took ([0-9.]+) seconds", text),
            "analytic_placement": optional_match(r"^## Analytic Placement took ([0-9.]+) seconds", text),
            "placement_quench": optional_match(r"^## Placement Quench took ([0-9.]+) seconds", text),
            "routing": optional_match(r"^# Routing took ([0-9.]+) seconds", text),
            "timing_analysis": optional_match(r"^Flow timing analysis took ([0-9.]+) seconds", text),
            "vpr_entire_flow": match(
                r"The entire flow of VPR took ([0-9.]+) seconds", text, "entire-flow time", float
            ),
        },
    }


def moved_blocks(reference_place: Path, output_place: Path) -> dict[str, int]:
    _reference_header, reference_rows = parse_place(reference_place)
    _output_header, output_rows = parse_place(output_place)
    reference = {row["name"]: row for row in reference_rows}
    output = {row["name"]: row for row in output_rows}
    if reference.keys() != output.keys():
        raise ContractError("VPR placement block names differ from the contract reference placement")
    location_fields = ("x", "y", "subtile", "layer")
    moved = sum(
        any(reference[name][field] != output[name][field] for field in location_fields)
        for name in reference
    )
    return {"blocks": len(reference), "moved_from_reference": moved}


def require_empty_work(path: Path) -> Path:
    work = path.resolve()
    if work.exists() and any(work.iterdir()):
        raise ContractError(f"work directory is not empty: {work}")
    work.mkdir(parents=True, exist_ok=True)
    return work


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mode", choices=("conventional", "analytic"), required=True)
    parser.add_argument("--case", required=True)
    parser.add_argument("--contract", type=Path, required=True)
    parser.add_argument("--vpr", type=Path, required=True)
    parser.add_argument("--architecture", type=Path, required=True)
    parser.add_argument("--circuit", type=Path, required=True)
    parser.add_argument("--netlist", type=Path, required=True)
    parser.add_argument("--reference-place", type=Path, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--channel-width", type=int, required=True)
    parser.add_argument("--expected-vpr-revision", required=True)
    parser.add_argument("--expected-vpr-sha256", required=True)
    parser.add_argument("extra_vpr_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    extra_vpr_args = args.extra_vpr_args[1:] if args.extra_vpr_args[:1] == ["--"] else args.extra_vpr_args

    try:
        forbidden = {"--pack", "--analytical_place", "--place", "--route", "--analysis", AP_OPTION}
        overlap = sorted(forbidden.intersection(extra_vpr_args))
        if overlap:
            raise ContractError(f"stage/placer options are controlled by the runner: {', '.join(overlap)}")

        contract = args.contract.resolve()
        manifest_path = absolute_file(contract / "manifest.json")
        manifest = json.loads(manifest_path.read_text())
        vpr = absolute_file(args.vpr)
        architecture = absolute_file(args.architecture)
        circuit = absolute_file(args.circuit)
        netlist = absolute_file(args.netlist)
        reference_place = absolute_file(args.reference_place)
        input_hashes = {
            "manifest": sha256(manifest_path),
            "vpr": sha256(vpr),
            "architecture": sha256(architecture),
            "circuit": sha256(circuit),
            "netlist": sha256(netlist),
            "reference_place": sha256(reference_place),
        }
        if input_hashes["vpr"] != args.expected_vpr_sha256:
            raise ContractError("VPR binary hash does not match --expected-vpr-sha256")
        if input_hashes["architecture"] != manifest["inputs"]["architecture"]["sha256"]:
            raise ContractError("architecture does not match the contract manifest")
        if input_hashes["netlist"] != manifest["inputs"]["packed_netlist"]["sha256"]:
            raise ContractError("packed netlist does not match the contract manifest")
        if input_hashes["reference_place"] != manifest["inputs"]["reference_place"]["sha256"]:
            raise ContractError("reference placement does not match the contract manifest")
        if manifest["packed_netlist"].get("architecture_id") != f"SHA256:{input_hashes['architecture']}":
            raise ContractError("architecture does not match the packed-netlist architecture id")
        if manifest["packed_netlist"].get("atom_netlist_id") != f"SHA256:{input_hashes['circuit']}":
            raise ContractError("circuit does not match the packed-netlist atom-netlist id")
        if args.seed != manifest["vpr"]["seed"] or args.channel_width != manifest["vpr"]["channel_width"]:
            raise ContractError("seed/channel width do not match the contract manifest")
        reference_validation = validate_contract(contract, reference_place)

        version_process = subprocess.run([str(vpr), "--version"], text=True, capture_output=True, check=False)
        version_text = version_process.stdout + version_process.stderr
        if version_process.returncode != 0:
            raise ContractError(f"VPR --version exited with status {version_process.returncode}")
        vpr_version = match(r"^Version:\s+(.+)$", version_text, "VPR version")
        vpr_revision = match(r"^Revision:\s+(.+)$", version_text, "VPR revision")
        if vpr_revision != args.expected_vpr_revision:
            raise ContractError(
                f"VPR revision {vpr_revision!r} does not equal expected revision {args.expected_vpr_revision!r}"
            )
        help_process = subprocess.run([str(vpr), "--help"], text=True, capture_output=True, check=False)
        help_text = help_process.stdout + help_process.stderr
        if help_process.returncode != 0 or AP_OPTION not in help_text:
            raise ContractError("VPR help does not expose the cluster-level analytic placer option")

        work = require_empty_work(args.work)
        work_netlist = work / "vpr_input.net"
        output_place = work / "vpr_output.place"
        output_route = work / "vpr_output.route"
        post_routing_netlist = work / "vpr_input.net.post_routing"
        native_macros = work / "place_macros.echo"
        stdout_path = work / "vpr.stdout.log"
        stderr_path = work / "vpr.stderr.log"
        shutil.copyfile(netlist, work_netlist)

        analytic_enabled = args.mode == "analytic"
        command = [
            str(vpr),
            str(architecture),
            str(circuit),
            "--net_file",
            str(work_netlist),
            "--place_file",
            str(output_place),
            "--route_file",
            str(output_route),
            "--seed",
            str(args.seed),
            "--num_workers",
            "1",
            "--route_chan_width",
            str(args.channel_width),
            "--echo_file",
            "on",
            AP_OPTION,
            "true" if analytic_enabled else "false",
        ]
        constraint_record = None
        if "vpr_constraints" in manifest.get("inputs", {}):
            constraint_path = absolute_file(Path(manifest["inputs"]["vpr_constraints"]["path"]))
            constraint_hash = sha256(constraint_path)
            if constraint_hash != manifest["inputs"]["vpr_constraints"]["sha256"]:
                raise ContractError("VPR constraints hash does not match the contract manifest")
            command.extend(["--read_vpr_constraints", str(constraint_path)])
            constraint_record = {"path": str(constraint_path), "sha256": constraint_hash}
        command.extend(extra_vpr_args)
        command.extend(["--place", "--route", "--analysis"])

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
        ap_markers = {"start": AP_START_MARKER in combined, "timer": AP_TIMER_MARKER in combined}
        if analytic_enabled and not all(ap_markers.values()):
            raise ContractError("analytic mode did not emit both cluster-level analytic placer execution markers")
        if not analytic_enabled and any(ap_markers.values()):
            raise ContractError("conventional mode unexpectedly executed the cluster-level analytic placer")
        for required in (output_place, output_route, post_routing_netlist, native_macros):
            if not required.is_file():
                raise ContractError(f"VPR did not create required output: {required}")
        if sha256(work_netlist) != input_hashes["netlist"]:
            raise ContractError("VPR modified the isolated pre-routing packed netlist copy")
        if sha256(native_macros) != manifest["inputs"]["native_macros"]["sha256"]:
            raise ContractError("VPR regenerated placement macros differ from the contract input")
        placement_validation = validate_contract(contract, output_place)
        movement = moved_blocks(reference_place, output_place)
        for path, before in (
            (architecture, input_hashes["architecture"]),
            (circuit, input_hashes["circuit"]),
            (netlist, input_hashes["netlist"]),
            (reference_place, input_hashes["reference_place"]),
        ):
            if sha256(path) != before:
                raise ContractError(f"VPR modified archived input: {path}")

        metrics = parse_vpr_metrics(combined)
        report = {
            "schema": "TILEPLACE_VPR_PLACEMENT_BASELINE_V1",
            "status": "pass",
            "case": args.case,
            "mode": args.mode,
            "method": "vpr_cluster_level_analytic_plus_quench" if analytic_enabled else "vpr_simulated_annealing",
            "same_packed_netlist": True,
            "integrated_analytical_place": False,
            "legal": True,
            "command": command,
            "returncode": process.returncode,
            "wall_s": wall_s,
            "seed": args.seed,
            "channel_width": args.channel_width,
            "num_workers": 1,
            **metrics,
            "placement": movement,
            "tool_validation": {
                "vpr_version": vpr_version,
                "vpr_revision": vpr_revision,
                "expected_vpr_revision": args.expected_vpr_revision,
                "expected_vpr_sha256": args.expected_vpr_sha256,
                "analytic_option_available": True,
                "analytic_enabled": analytic_enabled,
                "analytic_execution_markers": ap_markers,
            },
            "inputs": {
                "contract": {"path": str(contract), "manifest_sha256": input_hashes["manifest"]},
                "vpr": {"path": str(vpr), "sha256": input_hashes["vpr"]},
                "architecture": {"path": str(architecture), "sha256": input_hashes["architecture"]},
                "circuit": {"path": str(circuit), "sha256": input_hashes["circuit"]},
                "packed_netlist": {"path": str(netlist), "sha256": input_hashes["netlist"]},
                "reference_place": {"path": str(reference_place), "sha256": input_hashes["reference_place"]},
                **({"vpr_constraints": constraint_record} if constraint_record else {}),
            },
            "outputs": {
                "packed_netlist_copy": {"path": str(work_netlist), "sha256": sha256(work_netlist)},
                "post_routing_netlist": {
                    "path": str(post_routing_netlist), "sha256": sha256(post_routing_netlist)
                },
                "place": {"path": str(output_place), "sha256": sha256(output_place)},
                "route": {"path": str(output_route), "sha256": sha256(output_route)},
                "native_macros": {"path": str(native_macros), "sha256": sha256(native_macros)},
                "stdout": {"path": str(stdout_path), "sha256": sha256(stdout_path)},
                "stderr": {"path": str(stderr_path), "sha256": sha256(stderr_path)},
            },
            "reference_validation": reference_validation,
            "placement_validation": placement_validation,
        }
        report_path = args.report.resolve()
        report_path.parent.mkdir(parents=True, exist_ok=True)
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps(report, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"run_vpr_placement_baseline: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
