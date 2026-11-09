#!/usr/bin/env python3
"""Frozen-source paired CPU experiment; all algorithm work runs in C++."""
import argparse
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import time

from run_native_case import sha256
from native_base_costs import verify_export


def main():
    p = argparse.ArgumentParser()
    p.add_argument("case", type=Path)
    p.add_argument("reference", type=Path)
    p.add_argument("output", type=Path)
    p.add_argument("--modes", nargs="+", choices=("flat", "hierarchical", "downstream", "downstream_bounded"), default=["flat", "hierarchical"])
    p.add_argument("--timing-vpr", type=Path, help="VPR binary with the PersistRoute Tatum delay override hook")
    p.add_argument("--tree-timing-weight-q", type=int, default=0,
                   help="Q8 upstream route-tree delay weight; 256 includes full weighted delay")
    p.add_argument("--geometry-weight", type=int, default=64,
                   help="Corridor ranking distance weight; development ablation only")
    p.add_argument("--native-base-costs", type=Path, help="verified native indexed-cost export for this case")
    p.add_argument("--cost-model", choices=("additive", "vpr_style"), default="additive")
    p.add_argument("--cost-bits", type=int, choices=(16, 64), default=16)
    p.add_argument("--speculative-workers", type=int, default=0, help="0 selects serial; 1..32 CPU speculative workers")
    p.add_argument("--shadow-sync-windows", type=int, default=1, help="boundary summary publication period in speculative windows")
    a = p.parse_args()
    if not 0 <= a.speculative_workers <= 32 or not 1 <= a.shadow_sync_windows <= 0xffffffff:
        p.error("invalid speculative workers/shadow sync interval")
    if not 0 <= a.tree_timing_weight_q <= 65535:
        p.error("--tree-timing-weight-q must fit u16")
    if not 0 <= a.geometry_weight <= 0xffffffff:
        p.error("--geometry-weight must fit u32")
    case, reference, out = a.case.resolve(), a.reference.resolve(), a.output.resolve()
    native = json.loads((case / "run.json").read_text())
    baseline = json.loads((reference / "reference.json").read_text())
    if native["status"] != "passed" or baseline["status"] != "passed" or baseline["case"] != str(case):
        raise ValueError("native case and PR reference mismatch")
    for base, records in ((case, native["artifacts"]), (reference, baseline["artifacts"])):
        for rel, meta in records.items():
            if sha256(base / rel) != meta["sha256"]:
                raise ValueError(f"frozen input changed: {base / rel}")
    if a.native_base_costs:
        a.native_base_costs = a.native_base_costs.resolve()
        verify_export(a.native_base_costs, case)
    out.mkdir(parents=True, exist_ok=False)
    project = Path(__file__).resolve().parents[1]
    frozen = out / "source" / "dieroute"
    for directory in ("src", "include", "host", "tools", "tb"):
        (frozen / directory).mkdir(parents=True)
        for file in sorted((project / directory).iterdir()):
            if file.is_file(): shutil.copyfile(file, frozen / directory / file.name)
    shutil.copyfile(project / "CMakeLists.txt", frozen / "CMakeLists.txt")
    for directory in ("src", "include"):
        dest = out / "source/persistroute" / directory
        dest.mkdir(parents=True)
        for file in sorted((project.parent / "persistroute" / directory).iterdir()):
            if file.is_file(): shutil.copyfile(file, dest / file.name)
    adapter = out / "source/persistroute/tools/vpr_timing_analyzer.py"
    adapter.parent.mkdir(parents=True)
    shutil.copyfile(project.parent / "persistroute/tools/vpr_timing_analyzer.py", adapter)
    record = {"schema": "dieroute.rr_pair.v1", "status": "running", "case": str(case),
              "reference": str(reference), "board_result": False,
              "configuration": {"repeats": 5, "issue_width": 4, "repair_attempts": 8,
                                "geometry_weight": a.geometry_weight, "max_iterations": 30,
                                "route_tree_timing_weight_q": a.tree_timing_weight_q,
                                "base_cost_model": "native_indexed_ps" if a.native_base_costs else "uniform_pr",
                                "cost_model": a.cost_model,
                                "cost_state_bits": a.cost_bits,
                                "speculative_workers": a.speculative_workers, "shadow_sync_windows": a.shadow_sync_windows,
                                "criticality_cap_q": 64880 if a.cost_model == "vpr_style" else 65535,
                                "initial_criticality_q": 32768, "timing_updates": a.timing_vpr is not None,
                                "min_timing_iterations": 3 if a.timing_vpr else 1},
              "source_sha256": {str(f.relative_to(out)): sha256(f) for f in sorted((out / "source").rglob("*")) if f.is_file()},
              "native_run_sha256": sha256(case / "run.json"), "reference_sha256": sha256(reference / "reference.json"),
              "steps": [], "modes": {}}
    manifest = out / "pair.json"
    if a.native_base_costs:
        record["native_cost_export"] = {"path": str(a.native_base_costs),
                                        "sha256": sha256(a.native_base_costs / "costs.json")}
    timing_environment = {}
    if a.timing_vpr:
        timing_vpr = a.timing_vpr.resolve()
        record["timing_vpr"] = {"path": str(timing_vpr), "sha256": sha256(timing_vpr)}
        timing_environment = {
            "PERSISTROUTE_TIMING_COMMAND": shlex.join([sys.executable, str(adapter)]),
            "PERSISTROUTE_VPR_BIN": str(timing_vpr),
            "PERSISTROUTE_VPR_ARCH": str(case / "architecture.xml"),
            "PERSISTROUTE_VPR_CIRCUIT": str(case / "circuit.blif"),
            "PERSISTROUTE_VPR_NET": str(case / "circuit.net"),
            "PERSISTROUTE_VPR_PLACE": str(case / "circuit.place"),
            "PERSISTROUTE_VPR_ROUTE": str(case / "circuit.route"),
            "PERSISTROUTE_VPR_RR_GRAPH": str(case / "rr_graph.xml"),
            "PERSISTROUTE_VPR_CHAN_WIDTH": native["command"][native["command"].index("--route_chan_width") + 1],
            "DIEROUTE_MIN_TIMING_ITERATIONS": "3",
            "DIEROUTE_TIMING_UPDATE_PERIOD": "1",
        }
        record["timing_environment"] = timing_environment

    def save():
        manifest.write_text(json.dumps(record, indent=2) + "\n")

    def run(label, command, required=True):
        command = [str(x) for x in command]
        entry = {"label": label, "command": command, "cwd": str(out), "status": "running"}
        record["steps"].append(entry)
        env = {k: v for k, v in os.environ.items() if not k.startswith(("DIEROUTE_", "PERSISTROUTE_"))}
        env.update(timing_environment)
        env["DIEROUTE_TREE_TIMING_WEIGHT_Q"] = str(a.tree_timing_weight_q)
        env["DIEROUTE_GEOMETRY_WEIGHT"] = str(a.geometry_weight)
        entry['routing_environment'] = {key: value for key, value in env.items()
                                        if key.startswith(('DIEROUTE_', 'PERSISTROUTE_'))}
        env["DIEROUTE_VPR_STYLE_COST"] = str(int(a.cost_model == "vpr_style"))
        env["DIEROUTE_COST_BITS"] = str(a.cost_bits)
        env["DIEROUTE_SPECULATIVE_WORKERS"] = str(a.speculative_workers)
        env["DIEROUTE_SHADOW_SYNC_WINDOWS"] = str(a.shadow_sync_windows)
        start = time.monotonic_ns()
        with (out / (label + ".log")).open("w") as log:
            child = subprocess.Popen(command, cwd=out, env=env, stdout=log, stderr=subprocess.STDOUT)
            entry["pid"] = child.pid
            save()
            code = child.wait()
        entry.update(returncode=code, elapsed_ns=time.monotonic_ns() - start,
                     status="passed" if code == 0 else "failed", log_sha256=sha256(out / (label + ".log")))
        save()
        if required and code:
            raise RuntimeError(f"{label} failed: {out / (label + '.log')}")
        return code

    try:
        build = out / "build"
        run("configure", ["cmake", "-S", frozen, "-B", build, "-DCMAKE_BUILD_TYPE=Release"])
        run("build", ["cmake", "--build", build, "--target", "dieroute_rr", "-j4"])
        record["binary_sha256"] = sha256(build / "dieroute_rr")
        run("topology", [sys.executable, frozen / "tools/export_vpr_topology.py", case / "rr_graph.xml",
                         out / "topology", "--connections", reference / "connections.csv"])
        input_prefix = reference / "input"
        if a.native_base_costs:
            input_prefix = out / "input"
            run("rebase_costs", [sys.executable, frozen / "tools/native_base_costs.py", "rebase",
                                a.native_base_costs, reference / "input", input_prefix])
            record["rebased_input_sha256"] = sha256(out / "input.costs.json")
        text = (case / "vpr.log").read_text()
        wl = int(re.findall(r"Total wirelength:\s+(\d+)", text)[-1])
        cpd = float(re.findall(r"Final critical path delay \(least slack\):\s+([0-9.eE+-]+) ns", text)[-1])
        vpr = Path(native["sources"]["vpr"]["path"])
        if sha256(vpr) != native["sources"]["vpr"]["sha256"]: raise ValueError("VPR changed")
        width = native["command"][native["command"].index("--route_chan_width") + 1]
        # Use the already-frozen PR converters; their hashes were checked above.
        converters = reference / "source/tools"
        for mode in a.modes:
            hashes, reports = [], []
            state = {"status": "running", "runs": reports, "hashes": hashes}
            record["modes"][mode] = state
            for repeat in range(5):
                prefix = out / f"{mode}_{repeat}"
                code = run(f"{mode}_{repeat}", [build / "dieroute_rr", input_prefix, out / "topology", prefix, mode], required=False)
                if code not in (0, 3): raise RuntimeError(f"{mode} crashed or rejected input")
                reports.append(json.loads(Path(str(prefix) + ".json").read_text()))
                hashes.append({ext: sha256(Path(str(prefix) + "." + ext)) for ext in
                               ("paths.csv", "route_trees.csv", "resources", "costs", "iterations.csv", "audit.csv", "timing_iterations.csv", "transactions.csv")})
            state["deterministic"] = all(h == hashes[0] for h in hashes)
            semantic = [{k: v for k, v in r.items() if k != "wall_ms"} for r in reports]
            state["deterministic_counters"] = all(s == semantic[0] for s in semantic)
            state["legal"] = all(r["legal"] for r in reports)
            if not state["deterministic"] or not state["deterministic_counters"]:
                raise RuntimeError("semantic repeat mismatch")
            if not state["legal"]:
                state["status"] = "routing_failed"
                save()
                continue
            run(mode + "_write", [sys.executable, converters / "write_vpr_route.py", case / "circuit.route",
                 case / "rr_graph.xml", reference / "connections.csv", out / f"{mode}_0.route_trees.csv", out / f"{mode}.route"])
            run(mode + "_validate", [sys.executable, converters / "validate_vpr_route.py", "--vpr", vpr,
                "--arch", case / "architecture.xml", "--circuit", case / "circuit.blif", "--net", case / "circuit.net",
                "--place", case / "circuit.place", "--route", out / f"{mode}.route", "--rr-graph", case / "rr_graph.xml",
                "--channel-width", width, "--work-dir", out / (mode + "_validation"),
                "--baseline-wirelength", str(wl), "--baseline-cpd-ns", str(cpd)])
            state["native_validation"] = json.loads((out / (mode + "_validation") / "validation.json").read_text())
            state["status"] = "passed"
            save()
        record["status"] = "completed"  # completed measurement, not a passed QoR gate
    except Exception as error:
        record.update(status="failed", error=str(error))
        raise
    finally:
        save()
    print(json.dumps({"manifest": str(manifest), "status": record["status"],
                      "modes": {k: {f: v[f] for f in ("status", "deterministic", "legal")} for k, v in record["modes"].items()}}))


if __name__ == "__main__":
    main()
