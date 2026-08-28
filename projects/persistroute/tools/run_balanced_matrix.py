#!/usr/bin/env python3
"""Run a frozen/resumable every-round-STA PersistRoute matrix.

Every case is resumable at the RR-graph, packing, routing, route-writeback, and
native-VPR validation boundaries. Large generated artifacts stay in the output
directory; the aggregate JSON is the compact evidence intended for Git.
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_VPR = Path("/home/gry/.local/opt/vtr-9.0.0-src/build_vpr/vpr/vpr")


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1 << 20), b""):
            digest.update(block)
    return digest.hexdigest()


def resolve(path: str, base: Path = ROOT) -> Path:
    value = Path(path).expanduser()
    return value.resolve() if value.is_absolute() else (base / value).resolve()


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(path.suffix + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    temporary.replace(path)


def run(command: list[str], cwd: Path, stdout: Path, stderr: Path,
        env: dict[str, str] | None = None) -> tuple[int, float]:
    cwd.mkdir(parents=True, exist_ok=True)
    begin = time.perf_counter()
    with stdout.open("w", encoding="utf-8") as out, stderr.open("w", encoding="utf-8") as err:
        completed = subprocess.run(command, cwd=cwd, env=env, stdout=out, stderr=err, check=False)
    return completed.returncode, time.perf_counter() - begin


def require_files(paths: list[Path]) -> None:
    missing = [str(path) for path in paths if not path.is_file()]
    if missing:
        raise FileNotFoundError("missing input(s): " + ", ".join(missing))


def last_json_line(path: Path) -> dict:
    for line in reversed(path.read_text(encoding="utf-8").splitlines()):
        if line.lstrip().startswith("{"):
            return json.loads(line)
    raise ValueError(f"no JSON result in {path}")


def generate_rr_graph(case: dict, inputs: dict[str, Path], target: Path, vpr: Path,
                      log_dir: Path) -> dict:
    command = [
        str(vpr), str(inputs["architecture"]), str(inputs["circuit"]), "--analysis",
        "--net_file", str(inputs["net"]), "--place_file", str(inputs["place"]),
        "--route_file", str(inputs["route"]), "--route_chan_width", str(case["channel_width"]),
        "--write_rr_graph", str(target),
    ]
    if inputs.get("sdc"):
        command.extend(("--sdc_file", str(inputs["sdc"])))
    code, wall = run(command, log_dir, log_dir / "rr_graph.stdout", log_dir / "rr_graph.stderr")
    if code or not target.is_file():
        raise RuntimeError(f"RR graph generation failed with exit {code}")
    return {"command": command, "wall_s": wall, "sha256": sha256(target), "bytes": target.stat().st_size}


def run_case(case: dict, config: dict, output: Path, vpr: Path, host: Path) -> dict:
    case_dir = output / case["id"]
    input_dir = case_dir / "input"
    run_dir = case_dir / "run"
    native_dir = case_dir / "native_validation"
    for directory in (input_dir, run_dir, native_dir):
        directory.mkdir(parents=True, exist_ok=True)
    status_path = case_dir / "case_result.json"

    baseline_dir = resolve(case["baseline_dir"])
    source_inputs = {
        "architecture": resolve(case["architecture"]),
        "circuit": resolve(case["circuit"]),
        "net": resolve(case["net_path"]) if case.get("net_path") else baseline_dir / case["net"],
        "place": resolve(case["place_path"]) if case.get("place_path") else baseline_dir / case["place"],
        "route": resolve(case["route_path"]) if case.get("route_path") else baseline_dir / case["route"],
    }
    if case.get("sdc"):
        source_inputs["sdc"] = resolve(case["sdc"])
    require_files(list(source_inputs.values()) + [vpr, host])
    inputs = {name: source_inputs[name] for name in ("architecture", "circuit")}
    reference_dir = input_dir / "reference"
    reference_dir.mkdir(parents=True, exist_ok=True)
    for name in ("net", "place", "route", "sdc"):
        if name not in source_inputs:
            continue
        source = source_inputs[name]
        target = reference_dir / source.name
        if not target.is_file() or sha256(target) != sha256(source):
            shutil.copy2(source, target)
        inputs[name] = target

    record = {
        "schema": "PERSISTROUTE_BALANCED_MATRIX_CASE_V1",
        "case_id": case["id"], "name": case["name"], "suite": case["suite"],
        "status": "running", "configuration": config,
        "baseline": {"wirelength": case["baseline_wirelength"], "cpd_ns": case["baseline_cpd_ns"]},
        "inputs": {name: {"path": str(path), "sha256": sha256(path)} for name, path in inputs.items()},
        "source_inputs": {name: {"path": str(path), "sha256": sha256(path)}
                          for name, path in source_inputs.items()},
        "stages": {},
    }
    write_json(status_path, record)

    if case.get("rr_graph"):
        rr_graph = resolve(case["rr_graph"])
        require_files([rr_graph])
        record["stages"]["rr_graph"] = {"status": "reused", "path": str(rr_graph),
                                                 "sha256": sha256(rr_graph), "bytes": rr_graph.stat().st_size}
    else:
        rr_graph = input_dir / "rr_graph.xml"
        if rr_graph.is_file():
            record["stages"]["rr_graph"] = {"status": "resumed", "path": str(rr_graph),
                                                     "sha256": sha256(rr_graph), "bytes": rr_graph.stat().st_size}
        else:
            record["stages"]["rr_graph"] = {"status": "pass", **generate_rr_graph(
                case, inputs, rr_graph, vpr, case_dir / "rr_graph_generation")}
    write_json(status_path, record)

    connections = input_dir / "connections.csv"
    if not connections.is_file():
        command = [sys.executable, str(ROOT / "tools/vpr_route_connections.py"),
                   str(inputs["route"]), str(connections)]
        code, wall = run(command, input_dir, input_dir / "connections.stdout", input_dir / "connections.stderr")
        if code:
            raise RuntimeError(f"connection extraction failed with exit {code}")
        record["stages"]["connections"] = {"status": "pass", "command": command, "wall_s": wall}
    else:
        record["stages"]["connections"] = {"status": "resumed"}

    timing_env = os.environ.copy()
    timing_env.update({
        "PERSISTROUTE_VPR_BIN": str(vpr),
        "PERSISTROUTE_VPR_ARCH": str(inputs["architecture"]),
        "PERSISTROUTE_VPR_CIRCUIT": str(inputs["circuit"]),
        "PERSISTROUTE_VPR_NET": str(inputs["net"]),
        "PERSISTROUTE_VPR_PLACE": str(inputs["place"]),
        "PERSISTROUTE_VPR_ROUTE": str(inputs["route"]),
        "PERSISTROUTE_VPR_RR_GRAPH": str(rr_graph),
        "PERSISTROUTE_VPR_CHAN_WIDTH": str(case["channel_width"]),
    })
    if inputs.get("sdc"):
        timing_env["PERSISTROUTE_VPR_SDC"] = str(inputs["sdc"])

    if config.get("initial_reference_timing"):
        reference_input = input_dir / "reference_timing.input.csv"
        reference_output = input_dir / "reference_timing.output.csv"
        with connections.open(encoding="utf-8-sig", newline="") as source, \
                reference_input.open("w", encoding="utf-8", newline="") as target:
            rows = csv.DictReader(source)
            writer = csv.writer(target)
            writer.writerow(("iteration", "task_id", "net_id", "source", "sink",
                             "routed", "delay_ps", "criticality_q"))
            for row in rows:
                writer.writerow((0xffffffff, row["id"], row["net_id"], row["source"],
                                 row["sink"], 0, 0, row["criticality_q"]))
        command = [sys.executable, str(ROOT / "tools/vpr_timing_analyzer.py"),
                   str(0xffffffff), str(reference_input), str(reference_output)]
        code, wall = run(command, input_dir, input_dir / "reference_timing.stdout",
                         input_dir / "reference_timing.stderr", timing_env)
        if code:
            raise RuntimeError(f"reference timing initialization failed with exit {code}")
        criticalities = {}
        with reference_output.open(encoding="utf-8", newline="") as stream:
            for row in csv.DictReader(stream):
                criticalities[row["task_id"]] = row["criticality_q"]
        timed_connections = input_dir / "timed_connections.csv"
        temporary = timed_connections.with_suffix(".csv.tmp")
        with connections.open(encoding="utf-8-sig", newline="") as source, \
                temporary.open("w", encoding="utf-8", newline="") as target:
            rows = csv.DictReader(source)
            writer = csv.DictWriter(target, fieldnames=rows.fieldnames)
            writer.writeheader()
            for row in rows:
                if row["id"] not in criticalities:
                    raise RuntimeError(f"reference timing omitted task {row['id']}")
                row["criticality_q"] = criticalities[row["id"]]
                writer.writerow(row)
        temporary.replace(timed_connections)
        connections = timed_connections
        record["stages"]["reference_timing"] = {
            "status": "pass", "command": command, "wall_s": wall,
            "connections": len(criticalities), "output_sha256": sha256(reference_output),
        }

    prefix = input_dir / "vpr_input"
    manifest = input_dir / "vpr_input.manifest.json"
    packed = [prefix.with_suffix(suffix) for suffix in (".nodes", ".edges", ".resources", ".tasks")]
    packed_current = False
    if manifest.is_file() and all(path.is_file() for path in packed):
        prior_manifest = json.loads(manifest.read_text(encoding="utf-8"))
        packed_current = (prior_manifest.get("base_cost_q") == config["base_cost_q"]
                          and prior_manifest.get("connections_sha256") == sha256(connections))
    if not packed_current:
        command = [sys.executable, str(ROOT / "tools/pack_hls_inputs.py"), str(rr_graph),
                   str(connections), str(prefix), "--base-cost-q", str(config["base_cost_q"])]
        code, wall = run(command, input_dir, input_dir / "pack.stdout", input_dir / "pack.stderr")
        if code:
            raise RuntimeError(f"input packing failed with exit {code}")
        record["stages"]["packing"] = {"status": "pass", "command": command, "wall_s": wall}
    else:
        record["stages"]["packing"] = {"status": "resumed"}
    manifest_doc = json.loads(manifest.read_text(encoding="utf-8"))
    record["packed_input"] = {"manifest_sha256": sha256(manifest), **manifest_doc["files"]}
    write_json(status_path, record)

    routed_prefix = run_dir / case["name"]
    host_stdout, host_stderr = run_dir / "host.stdout", run_dir / "host.stderr"
    route_trees = routed_prefix.with_suffix(".route_trees.csv")
    host_result_path = run_dir / "host_result.json"
    def execution_config(value: dict) -> dict:
        return {key: item for key, item in value.items()
                if not key.startswith(("balanced_", "relaxed_"))
                and not (key == "initial_reference_timing" and not item)}
    run_identity = {"configuration": execution_config(config), "host_sha256": sha256(host)}
    reusable_host_result = False
    if host_result_path.is_file() and route_trees.is_file():
        prior_identity = json.loads(host_result_path.read_text(encoding="utf-8")).get("run_identity", {})
        reusable_host_result = (
            prior_identity.get("host_sha256") == run_identity["host_sha256"]
            and execution_config(prior_identity.get("configuration", {})) == run_identity["configuration"])
    host_ran = not reusable_host_result
    if host_ran:
        env = timing_env.copy()
        env.update({
            "PERSISTROUTE_PE_COUNT": str(config["pe_count"]),
            "PERSISTROUTE_ISSUE_WIDTH": str(config["issue_width"]),
            "PERSISTROUTE_ADAPTIVE_ISSUE_MIN": str(config.get("adaptive_issue_width_min", 0)),
            "PERSISTROUTE_ADAPTIVE_ISSUE_STAGNATION": str(
                config.get("adaptive_issue_stagnation_iterations", 0)),
            "PERSISTROUTE_ADAPTIVE_ISSUE_TAIL_TASKS": str(
                config.get("adaptive_issue_tail_tasks", 0)),
            "PERSISTROUTE_MAX_ITERATIONS": str(config["max_iterations"]),
            "PERSISTROUTE_MIN_TIMING_ITERATIONS": str(config["min_timing_iterations"]),
            "PERSISTROUTE_TIMING_UPDATE_PERIOD": str(config["timing_update_period"]),
            "PERSISTROUTE_SELECTIVE_CLEANUP_PASSES": str(config["cleanup_passes"]),
            "PERSISTROUTE_TIMING_COMMAND": f"{sys.executable} {ROOT / 'tools/vpr_timing_analyzer.py'}",
        })
        command = [str(host), str(prefix), str(routed_prefix)]
        code, wall = run(command, run_dir, host_stdout, host_stderr, env)
        host_result = last_json_line(host_stdout)
        host_result.update({"exit_status": code, "wall_s_measured": wall, "command": command,
                            "run_identity": run_identity})
        write_json(host_result_path, host_result)
    else:
        host_result = json.loads(host_result_path.read_text(encoding="utf-8"))
    record["stages"]["hbm_cmodel"] = {"status": "pass" if host_result.get("legal") else "illegal",
                                               **host_result}
    write_json(status_path, record)
    if not host_result.get("legal"):
        record["status"] = "rejected_illegal"
        write_json(status_path, record)
        return record

    persist_route = run_dir / f"{case['name']}.persist.route"
    route_write = run_dir / "route_write.json"
    if host_ran or not persist_route.is_file() or not route_write.is_file():
        command = [sys.executable, str(ROOT / "tools/write_vpr_route.py"), str(inputs["route"]),
                   str(rr_graph), str(connections), str(route_trees), str(persist_route)]
        code, wall = run(command, run_dir, route_write, run_dir / "route_write.stderr")
        if code:
            raise RuntimeError(f"route writeback failed with exit {code}")
        record["stages"]["route_writeback"] = {"status": "pass", "command": command, "wall_s": wall}
    else:
        record["stages"]["route_writeback"] = {"status": "resumed"}

    validation = native_dir / "validation.json"
    if host_ran or not validation.is_file():
        command = [
            sys.executable, str(ROOT / "tools/validate_vpr_route.py"), "--vpr", str(vpr),
            "--arch", str(inputs["architecture"]), "--circuit", str(inputs["circuit"]),
            "--net", str(inputs["net"]), "--place", str(inputs["place"]),
            "--route", str(persist_route), "--rr-graph", str(rr_graph),
            "--channel-width", str(case["channel_width"]), "--work-dir", str(native_dir),
            "--report", str(validation), "--baseline-wirelength", str(case["baseline_wirelength"]),
            "--baseline-cpd-ns", str(case["baseline_cpd_ns"]),
        ]
        if inputs.get("sdc"):
            command.extend(("--sdc", str(inputs["sdc"])))
        code, wall = run(command, native_dir, native_dir / "validator.stdout", native_dir / "validator.stderr")
        if code:
            raise RuntimeError(f"native validation failed with exit {code}")
        record["stages"]["native_validation"] = {"status": "pass", "command": command, "wall_s": wall}
    else:
        record["stages"]["native_validation"] = {"status": "resumed"}
    validation_doc = json.loads(validation.read_text(encoding="utf-8"))
    record["native_validation"] = validation_doc
    record["balanced_case_pass"] = bool(
        validation_doc["legal"]
        and validation_doc["wirelength_delta_percent"] <= config["balanced_wirelength_delta_percent_max"]
        and validation_doc["cpd_delta_percent"] <= config["balanced_cpd_delta_percent_max"])
    record["relaxed_case_pass"] = bool(
        validation_doc["legal"]
        and validation_doc["wirelength_delta_percent"] <= config["relaxed_wirelength_delta_percent_max"]
        and validation_doc["cpd_delta_percent"] <= config["relaxed_cpd_delta_percent_max"])
    record["output_hashes"] = {
        path.name: sha256(path) for path in (
            routed_prefix.with_suffix(".paths.csv"), route_trees,
            routed_prefix.with_suffix(".resources"), persist_route, validation)
    }
    record["status"] = "pass" if record["balanced_case_pass"] else "qor_gate_fail"
    write_json(status_path, record)
    return record


def aggregate(config: dict, results: list[dict]) -> dict:
    validated = [item for item in results if item.get("native_validation", {}).get("legal")]
    def geomean_delta(key: str) -> float | None:
        if not validated:
            return None
        return 100.0 * (math.prod(1.0 + item["native_validation"][key] / 100.0
                                  for item in validated) ** (1.0 / len(validated)) - 1.0)
    return {
        "schema": "PERSISTROUTE_BALANCED_MATRIX_V1",
        "configuration": config,
        "case_count": len(results),
        "legal_case_count": len(validated),
        "balanced_case_count": sum(bool(item.get("balanced_case_pass")) for item in results),
        "relaxed_case_count": sum(bool(item.get("relaxed_case_pass")) for item in results),
        "all_cases_legal": len(validated) == len(results),
        "all_cases_pass_balanced_gate": bool(results) and all(item.get("balanced_case_pass") for item in results),
        "all_cases_pass_relaxed_gate": bool(results) and all(item.get("relaxed_case_pass") for item in results),
        "geomean_wirelength_delta_percent": geomean_delta("wirelength_delta_percent"),
        "geomean_cpd_delta_percent": geomean_delta("cpd_delta_percent"),
        "cases": results,
        "claim_boundary": "HBM C-model screening and native VPR QoR only; no physical-U280 speed or energy claim.",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=ROOT / "experiments/balanced_issue8_matrix_cases.json")
    parser.add_argument("--output", type=Path, default=ROOT / "experiments/balanced_issue8_matrix_2026-08-28")
    parser.add_argument("--summary", type=Path, default=ROOT / "experiments/balanced_issue8_matrix_2026-08-28.json")
    parser.add_argument("--vpr", type=Path, default=DEFAULT_VPR)
    parser.add_argument("--host", type=Path, default=ROOT / "host/persistroute_accelerated_cmodel")
    parser.add_argument("--case", action="append", dest="selected")
    parser.add_argument("--include-existing", action="store_true",
                        help="aggregate completed case_result.json files already in --output")
    parser.add_argument("--issue-width", type=int)
    parser.add_argument("--adaptive-issue-min", type=int)
    parser.add_argument("--adaptive-stagnation", type=int)
    parser.add_argument("--adaptive-tail-tasks", type=int)
    parser.add_argument("--initial-reference-timing", action=argparse.BooleanOptionalAction,
                        default=None)
    parser.add_argument("--max-iterations", type=int)
    args = parser.parse_args()
    document = json.loads(args.config.read_text(encoding="utf-8"))
    document["configuration"].setdefault("conflict_validation_read_set", "path_resources")
    document["configuration"].setdefault("relaxed_wirelength_delta_percent_max", 5)
    document["configuration"].setdefault("relaxed_cpd_delta_percent_max", 5)
    overrides = {
        "issue_width": args.issue_width,
        "adaptive_issue_width_min": args.adaptive_issue_min,
        "adaptive_issue_stagnation_iterations": args.adaptive_stagnation,
        "adaptive_issue_tail_tasks": args.adaptive_tail_tasks,
        "max_iterations": args.max_iterations,
        "initial_reference_timing": args.initial_reference_timing,
    }
    document["configuration"].update(
        {key: value for key, value in overrides.items() if value is not None})
    all_cases = document["cases"]
    cases = all_cases
    if args.selected:
        selected = set(args.selected)
        unknown = selected - {case["id"] for case in cases}
        if unknown:
            parser.error("unknown case(s): " + ", ".join(sorted(unknown)))
        cases = [case for case in cases if case["id"] in selected]
    results = []
    for case in cases:
        print(f"[balanced-matrix] {case['id']}", flush=True)
        try:
            results.append(run_case(case, document["configuration"], args.output.resolve(),
                                    args.vpr.resolve(), args.host.resolve()))
        except Exception as error:
            failure = {"schema": "PERSISTROUTE_BALANCED_MATRIX_CASE_V1", "case_id": case["id"],
                       "name": case["name"], "suite": case["suite"], "status": "error",
                       "error": str(error)}
            write_json(args.output.resolve() / case["id"] / "case_result.json", failure)
            results.append(failure)
            print(f"[balanced-matrix] ERROR {case['id']}: {error}", file=sys.stderr, flush=True)
        write_json(args.summary.resolve(), aggregate(document["configuration"], results))
    if args.include_existing:
        existing = []
        for case in all_cases:
            result_path = args.output.resolve() / case["id"] / "case_result.json"
            if result_path.is_file():
                item = json.loads(result_path.read_text(encoding="utf-8"))
                if item.get("status") not in ("running", "error"):
                    existing.append(item)
        write_json(args.summary.resolve(), aggregate(document["configuration"], existing))
    return 0 if results and all(item.get("status") == "pass" for item in results) else 3


if __name__ == "__main__":
    raise SystemExit(main())
