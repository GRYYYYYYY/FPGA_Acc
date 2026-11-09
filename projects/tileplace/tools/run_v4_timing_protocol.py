#!/usr/bin/env python3
"""Execute a sealed development timing protocol without modifying QoR evidence."""

from __future__ import annotations

import argparse
import json
import os
import platform
import statistics
import subprocess
import time
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, sha256


def signature(report: dict) -> dict:
    """Ignore artifact locations/timings while preserving every search decision."""
    return {
        "final_place_sha256": report["output_place"]["sha256"],
        "config": report["config"],
        "initial_route_feedback": report.get("initial_route_feedback"),
        "initial_timing_feedback": report.get("initial_timing_feedback"),
        "stop_reason": report["stop_reason"],
        "closure_calls": report["closure_calls"],
        "accepted_transactions": report["accepted_transactions"],
        "final": {k: report["final"][k] for k in ("legal", "cpd_ns", "wirelength")},
        "trials": [{k: t[k] for k in ("accepted", "reason", "transaction_ids", "transaction_count")}
                   | {"place_sha256": t["candidate_place"]["sha256"],
                      "cpd_ns": t["closure"].get("cpd_ns"), "wirelength": t["closure"].get("wirelength")}
                   for t in report["trials"]],
    }


def feedback_signature(report: dict) -> dict:
    provenance = report["provenance"]
    return {
        "initial_route": provenance["initial_route_feedback_sha256"],
        "initial_timing": provenance["initial_timing_feedback_sha256"],
        "refreshes": [{k: row[k] for k in ("route_feedback_sha256", "timing_feedback_sha256", "parser")}
                      for row in provenance["feedback_refreshes"]],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--protocol-sha256", required=True)
    args = parser.parse_args()
    if sha256(args.protocol) != args.protocol_sha256:
        raise ContractError("protocol seal mismatch")
    protocol = json.loads(args.protocol.read_text())
    if protocol["schema"] != "TILEPLACE_V4_DEVELOPMENT_TIMING_PROTOCOL_V1":
        raise ContractError("unsupported protocol")
    for record in protocol["files"]:
        if sha256(Path(record["path"])) != record["sha256"]:
            raise ContractError(f"sealed input/source changed: {record['path']}")
    cpu = protocol["cpu"]
    if cpu not in os.sched_getaffinity(0):
        raise ContractError("registered CPU unavailable")
    root = Path(protocol["output_root"])
    root.mkdir(parents=True, exist_ok=False)
    expected = signature(json.loads(Path(protocol["reference_report"]).read_text()))
    rows = []
    first_feedback_identity = None
    dump_json(root / "environment.json", {
        "uname": list(platform.uname()), "python": platform.python_version(),
        "affinity_before": sorted(os.sched_getaffinity(0)), "cpu": cpu,
        "cpuinfo": Path("/proc/cpuinfo").read_text(),
        "loadavg": Path("/proc/loadavg").read_text(),
        "protocol_sha256": args.protocol_sha256,
    })
    for index in range(protocol["warmups"] + protocol["measured_runs"]):
        run = root / f"run_{index:02d}"
        run.mkdir()
        command = [value.replace("{run_dir}", str(run)) for value in protocol["command"]]
        dump_json(run / "command.json", command)
        with (run / "stdout.log").open("w") as stdout, (run / "stderr.log").open("w") as stderr:
            start = time.perf_counter()
            process = subprocess.run(command, cwd=protocol["cwd"], stdout=stdout, stderr=stderr, check=False)
            external_wall = time.perf_counter() - start
        row = {"index": index, "warmup": index < protocol["warmups"],
               "returncode": process.returncode, "process_wall_s": external_wall}
        dump_json(run / "process.json", row)
        if process.returncode:
            raise ContractError(f"run {index} failed; retained evidence, no automatic retries")
        report = json.loads((run / "report.json").read_text())
        if "implementation_sha256" in protocol:
            provenance = report.get("provenance", {})
            if provenance.get("implementation", {}).get("sha256") != protocol["implementation_sha256"]:
                raise ContractError("run does not report the sealed implementation")
            if provenance.get("source_and_input_hashes_unchanged_at_completion") is not True:
                raise ContractError("run did not verify unchanged sources and inputs")
            identity = feedback_signature(report)
            if first_feedback_identity is None:
                first_feedback_identity = identity
            elif identity != first_feedback_identity:
                raise ContractError("feedback content differs between repeated runs")
        if signature(report) != expected or sha256(run / "final.place") != expected["final_place_sha256"]:
            raise ContractError(f"run {index} differs from frozen development search")
        timing = json.loads((run / "timing.json").read_text())
        if timing["report"]["sha256"] != sha256(run / "report.json"):
            raise ContractError("timing/report binding mismatch")
        row.update({"timing": timing, "search_matches_reference": True,
                    "timing_sha256": sha256(run / "timing.json"), "report_sha256": sha256(run / "report.json")})
        rows.append(row)
        dump_json(root / "progress.json", {"completed": rows})
        print(f"run {index}: {external_wall:.3f} s; exact search match; warmup={row['warmup']}", flush=True)
    measured = [r for r in rows if not r["warmup"]]
    times = [r["process_wall_s"] for r in measured]
    result = {"schema": "TILEPLACE_V4_DEVELOPMENT_TIMING_RESULT_V1", "status": "pass",
              "protocol_sha256": args.protocol_sha256, "case": protocol["case"],
              "implementation_sha256": protocol.get("implementation_sha256"),
              "runs": rows, "median_process_wall_s": statistics.median(times),
              "sample_cv_pct": 100 * statistics.stdev(times) / statistics.mean(times),
              "median_stage_wall_s": {k: statistics.median(r["timing"]["search_stage_wall_s"][k] for r in measured)
                                       for k in measured[0]["timing"]["search_stage_wall_s"]},
              "limitations": protocol["limitations"]}
    dump_json(root / "summary.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "runs"}, sort_keys=True))


if __name__ == "__main__":
    main()
