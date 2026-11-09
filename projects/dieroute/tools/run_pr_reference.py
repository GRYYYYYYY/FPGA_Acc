#!/usr/bin/env python3
"""Freeze and run the unpartitioned PR CPU reference on one native VPR case."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import time

from run_native_case import sha256


def main():
    p = argparse.ArgumentParser()
    p.add_argument("case", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--repeats", type=int, default=5)
    args = p.parse_args()
    if args.repeats < 5:
        p.error("at least five repeats are required")
    case, output = args.case.resolve(), args.output.resolve()
    native = json.loads((case / "run.json").read_text())
    if native["status"] != "passed":
        raise ValueError("native input case did not pass")
    for name, metadata in native["artifacts"].items():
        if sha256(case / name) != metadata["sha256"]:
            raise ValueError(f"native artifact changed: {name}")
    output.mkdir(parents=True, exist_ok=False)
    pr = Path(__file__).resolve().parents[2] / "persistroute"
    source = output / "source"
    files = [pr / "host/pathfinder_host.cpp", pr / "src/pathfinder.cpp", pr / "src/external_timing.cpp"]
    files += sorted((pr / "include").glob("*.hpp"))
    files += [pr / "tools" / name for name in (
        "vpr_route_connections.py", "pack_hls_inputs.py", "write_vpr_route.py", "validate_vpr_route.py")]
    frozen = {}
    for file in files:
        rel = file.relative_to(pr)
        target = source / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(file, target)
        frozen[str(rel)] = sha256(target)
    record = {"schema": "dieroute.pr_reference.v1", "case": str(case), "status": "running",
              "evidence_class": "unpartitioned_PR_CPU_reference_on_native_multidie",
              "board_result": False, "source_hashes": frozen, "steps": [],
              "configuration": {"base_cost_q": 64, "fixed_criticality_q": 32768,
                                "max_iterations": 30, "timing_updates": False},
              "native_run_sha256": sha256(case / "run.json")}
    manifest = output / "reference.json"

    def save():
        manifest.write_text(json.dumps(record, indent=2) + "\n")

    def run(label, command):
        command = [str(s) for s in command]
        step = {"label": label, "command": command, "cwd": str(output), "status": "running"}
        record["steps"].append(step)
        save()
        start = time.monotonic_ns()
        # Do not inherit an unrelated research run's parameter overrides.
        env = {k: v for k, v in os.environ.items() if not k.startswith("PERSISTROUTE_")}
        with (output / (label + ".log")).open("w") as log:
            completed = subprocess.run(command, cwd=output, env=env, stdout=log, stderr=subprocess.STDOUT)
        step.update(returncode=completed.returncode, elapsed_ns=time.monotonic_ns() - start,
                    status="passed" if completed.returncode == 0 else "failed",
                    log_sha256=sha256(output / (label + ".log")))
        save()
        if completed.returncode != 0:
            raise RuntimeError(f"{label} failed; see {output / (label + '.log')}")

    try:
        tools = source / "tools"
        run("compile", ["g++", "-std=c++17", "-O2", "-Wall", "-Wextra", "-I" + str(source / "include"),
                        source / "host/pathfinder_host.cpp", source / "src/pathfinder.cpp",
                        source / "src/external_timing.cpp", "-o", output / "pr_reference"])
        record["executable_sha256"] = sha256(output / "pr_reference")
        run("connections", [sys.executable, tools / "vpr_route_connections.py", case / "circuit.route",
                            output / "connections.csv", "--criticality-q", "32768"])
        run("pack", [sys.executable, tools / "pack_hls_inputs.py", case / "rr_graph.xml",
                     output / "connections.csv", output / "input", "--base-cost-q", "64"])
        run("topology", [sys.executable, Path(__file__).with_name("export_vpr_topology.py").resolve(),
                         case / "rr_graph.xml", output / "input", "--connections", output / "connections.csv"])
        deterministic = []
        for i in range(args.repeats):
            run(f"repeat_{i}", [output / "pr_reference", output / "input", output / f"repeat_{i}"])
            deterministic.append({suffix: sha256(output / f"repeat_{i}.{suffix}")
                                  for suffix in ("paths.csv", "route_trees.csv", "resources", "iterations.csv", "timing_iterations.csv")})
        record["repeat_hashes"] = deterministic
        record["deterministic"] = all(item == deterministic[0] for item in deterministic)
        if not record["deterministic"]:
            raise RuntimeError("repeat semantic hashes differ")
        run("write_route", [sys.executable, tools / "write_vpr_route.py", case / "circuit.route", case / "rr_graph.xml",
                            output / "connections.csv", output / "repeat_0.route_trees.csv", output / "reference.route"])
        text = (case / "vpr.log").read_text()
        wl = int(re.findall(r"Total wirelength:\s+(\d+)", text)[-1])
        cpd = float(re.findall(r"Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns", text)[-1])
        vpr = Path(native["sources"]["vpr"]["path"])
        if sha256(vpr) != native["sources"]["vpr"]["sha256"]:
            raise ValueError("VPR binary changed since baseline")
        cmd = native["command"]
        width = cmd[cmd.index("--route_chan_width") + 1]
        run("native_validation", [sys.executable, tools / "validate_vpr_route.py", "--vpr", vpr,
            "--arch", case / "architecture.xml", "--circuit", case / "circuit.blif",
            "--net", case / "circuit.net", "--place", case / "circuit.place",
            "--route", output / "reference.route", "--rr-graph", case / "rr_graph.xml",
            "--channel-width", width, "--work-dir", output / "native_validation",
            "--baseline-wirelength", str(wl), "--baseline-cpd-ns", str(cpd)])
        record["native_validation"] = json.loads((output / "native_validation/validation.json").read_text())
        record["topology"] = json.loads((output / "input.topology.json").read_text())
        record["status"] = "passed"
    except Exception as error:
        record.update(status="failed", error=str(error))
        raise
    finally:
        record["artifacts"] = {str(f.relative_to(output)): {"bytes": f.stat().st_size, "sha256": sha256(f)}
                               for f in sorted(output.rglob("*")) if f.is_file() and f != manifest}
        save()
    print(json.dumps({"manifest": str(manifest), "status": record["status"], "deterministic": record["deterministic"]}))


if __name__ == "__main__":
    main()
