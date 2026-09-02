#!/usr/bin/env python3
"""Freeze one externally sourced VPR placement-constraint experiment."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path
from types import SimpleNamespace

from tileplace_vpr import ContractError, dump_json, legalize, pack, sha256


def existing(path: Path) -> Path:
    resolved = path.resolve()
    if not resolved.is_file():
        raise ContractError(f"required file does not exist: {resolved}")
    return resolved


def match(pattern: str, text: str, label: str, cast: type = str):
    result = re.search(pattern, text, re.MULTILINE)
    if not result:
        raise ContractError(f"VPR log is missing {label}")
    return cast(result.group(1))


def ensure_new_directory(path: Path) -> Path:
    resolved = path.resolve()
    if resolved.exists() and any(resolved.iterdir()):
        raise ContractError(f"refusing to overwrite non-empty directory: {resolved}")
    resolved.mkdir(parents=True, exist_ok=True)
    return resolved


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--case-name", required=True)
    parser.add_argument("--vpr", type=Path, required=True)
    parser.add_argument("--architecture", type=Path, required=True)
    parser.add_argument("--circuit", type=Path, required=True)
    parser.add_argument("--vpr-constraints", type=Path, required=True)
    parser.add_argument("--source-revision", required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--channel-width", type=int, required=True)
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("extra_vpr_args", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    extra_vpr_args = args.extra_vpr_args[1:] if args.extra_vpr_args[:1] == ["--"] else args.extra_vpr_args

    try:
        vpr = existing(args.vpr)
        architecture = existing(args.architecture)
        circuit = existing(args.circuit)
        source_constraints = existing(args.vpr_constraints)
        work = ensure_new_directory(args.work)
        output = ensure_new_directory(args.output)

        archived_constraints = output / "source.vpr_constraints.xml"
        shutil.copyfile(source_constraints, archived_constraints)
        netlist = work / "baseline.net"
        reference_place = work / "baseline.place"
        route = work / "baseline.route"
        rr_graph = work / "rr_graph.xml"
        stdout_path = work / "baseline.stdout.log"
        stderr_path = work / "baseline.stderr.log"
        command = [
            str(vpr),
            str(architecture),
            str(circuit),
            "--net_file",
            str(netlist),
            "--place_file",
            str(reference_place),
            "--route_file",
            str(route),
            "--seed",
            str(args.seed),
            "--num_workers",
            "1",
            "--route_chan_width",
            str(args.channel_width),
            "--read_vpr_constraints",
            str(archived_constraints),
            "--write_rr_graph",
            str(rr_graph),
            "--echo_file",
            "on",
            *extra_vpr_args,
        ]
        start = time.monotonic()
        process = subprocess.run(command, cwd=work, text=True, capture_output=True, check=False)
        baseline_wall_s = time.monotonic() - start
        stdout_path.write_text(process.stdout)
        stderr_path.write_text(process.stderr)
        combined = process.stdout + process.stderr
        if process.returncode != 0:
            raise ContractError(f"baseline VPR exited with status {process.returncode}; see {stdout_path}")
        for marker in (
            "Completed placement consistency check successfully.",
            "Completed routing consistency check successfully.",
            "Circuit successfully routed with a channel width factor",
            "VPR succeeded",
        ):
            if marker not in combined:
                raise ContractError(f"baseline VPR success marker is missing: {marker}")
        native_echo = work / "place_macros.echo"
        for artifact in (netlist, reference_place, route, rr_graph, native_echo):
            if not artifact.is_file():
                raise ContractError(f"baseline VPR did not create {artifact}")

        archived_echo = output / "vpr_place_macros.echo"
        shutil.copyfile(native_echo, archived_echo)
        revision = match(r"^Revision:\s+(.+)$", combined, "VPR revision")
        pack(
            SimpleNamespace(
                netlist=netlist,
                place=reference_place,
                rr_graph=rr_graph,
                architecture=architecture,
                native_macros=archived_echo,
                connections=None,
                timing=None,
                constraints=None,
                vpr_constraints=archived_constraints,
                output=output,
                vpr_revision=revision,
                seed=args.seed,
                channel_width=args.channel_width,
                vpr_command=command,
            )
        )

        golden = output / f"{args.case_name}.golden.place"
        repeat = work / f"{args.case_name}.golden.repeat.place"
        golden_report = legalize(output, golden)
        repeat_report = legalize(output, repeat)
        if sha256(golden) != sha256(repeat):
            raise ContractError("CPU golden placement is not deterministic")
        dump_json(output / "golden_validation.json", golden_report)

        closure_report = output / "vpr_native_closure.json"
        closure_work = work / "native_closure"
        closure_command = [
            sys.executable,
            str(Path(__file__).with_name("run_vpr_closure.py")),
            "--contract",
            str(output),
            "--vpr",
            str(vpr),
            "--architecture",
            str(architecture),
            "--circuit",
            str(circuit),
            "--netlist",
            str(netlist),
            "--golden-place",
            str(golden),
            "--work",
            str(closure_work),
            "--report",
            str(closure_report),
            "--seed",
            str(args.seed),
            "--channel-width",
            str(args.channel_width),
        ]
        if extra_vpr_args:
            closure_command.extend(["--", *extra_vpr_args])
        closure = subprocess.run(closure_command, text=True, capture_output=True, check=False)
        (work / "closure.stdout.log").write_text(closure.stdout)
        (work / "closure.stderr.log").write_text(closure.stderr)
        if closure.returncode != 0:
            raise ContractError(
                f"native closure exited with status {closure.returncode}: {closure.stderr.strip()}"
            )
        native_closure = json.loads(closure_report.read_text())
        manifest = json.loads((output / "manifest.json").read_text())
        summary = {
            "schema": "TILEPLACE_EXTERNAL_CONSTRAINT_CASE_V1",
            "status": "pass",
            "case": args.case_name,
            "source": {
                "kind": "VTR regression placement constraint",
                "revision": args.source_revision,
                "original_path": str(source_constraints),
                "archived_path": str(archived_constraints),
                "sha256": sha256(archived_constraints),
            },
            "baseline": {
                "command": command,
                "wall_s": baseline_wall_s,
                "routing_iterations": match(
                    r"Successfully routed after (\d+) routing iterations", combined, "iteration count", int
                ),
                "wirelength": match(r"Total wirelength:\s+(\d+)", combined, "wirelength", int),
                "cpd_ns": match(
                    r"Final critical path delay \(least slack\):\s+([0-9.]+) ns",
                    combined,
                    "CPD",
                    float,
                ),
                "vpr_revision": revision,
            },
            "constraints": manifest["placement_constraints"],
            "contract": {
                "blocks": manifest["outputs"]["blocks.jsonl"]["count"],
                "sites": manifest["outputs"]["sites.jsonl"]["count"],
                "nets": manifest["outputs"]["nets.jsonl"]["count"],
                "macros": manifest["placement_macros"],
            },
            "cpu_golden": {
                **golden_report,
                "repeat_sha256": sha256(repeat),
                "deterministic_repeat": repeat_report == golden_report,
            },
            "native_closure": {
                "legal": native_closure["legal"],
                "routing_iterations": native_closure["routing_iterations"],
                "wirelength": native_closure["wirelength"],
                "cpd_ns": native_closure["cpd_ns"],
                "report": str(closure_report),
                "report_sha256": sha256(closure_report),
            },
            "claim_boundary": (
                "This case validates external VPR region/fixed-constraint import and native legality; "
                "it is not a TilePlace QoR or hardware-speedup result."
            ),
        }
        dump_json(output / "external_constraint_case.json", summary)
        print(json.dumps(summary, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"run_external_constraint_case: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
