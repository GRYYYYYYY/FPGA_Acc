#!/usr/bin/env python3
"""Audit sealed frontier arms and compute within-design QoR comparisons."""

import argparse
import json
import math
from pathlib import Path

from audit_fixed_development import audit_native_trials
from run_fixed_development import validate
from run_v4_timing_protocol import signature, feedback_signature
from tileplace_provenance import verify_files
from tileplace_vpr import ContractError, dump_json, sha256

PROTOCOL_SHA = "8e32b78f2078246a1ee7764e054bda5f6da8a3e35175d509e40286e531e1e7a7"


def audit_process(receipt):
    wall = receipt.get("process_wall_s")
    if receipt.get("returncode") != 0 or not isinstance(wall, (int, float)) or not math.isfinite(wall) or wall <= 0:
        raise ContractError("invalid or failed process receipt")


def compare_arms(enabled, disabled):
    for key in ("baseline", "config"):
        if enabled[key] != disabled[key]:
            raise ContractError(f"paired {key} differs")
    for key in ("inputs", "initial_route_feedback_sha256", "initial_timing_feedback_sha256"):
        if enabled["provenance"][key] != disabled["provenance"][key]:
            raise ContractError(f"paired {key} differs")
    settings = []
    for report, expected in ((enabled, True), (disabled, False)):
        value = dict(report["provenance"]["settings"])
        if value.pop("use_no_goods", None) is not expected:
            raise ContractError("wrong suppression arm")
        settings.append(value)
    if settings[0] != settings[1]:
        raise ContractError("paired search settings differ")
    return {"cpd_enabled_over_disabled": enabled["final"]["cpd_ns"] / disabled["final"]["cpd_ns"],
            "wirelength_enabled_over_disabled": enabled["final"]["wirelength"] / disabled["final"]["wirelength"]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    exp = Path(__file__).resolve().parents[1] / "experiments"
    path = exp / "tileplace_frontier_ablation_protocol_2026-09-29.json"
    if sha256(path) != PROTOCOL_SHA:
        raise ContractError("protocol seal mismatch")
    protocol = json.loads(path.read_text())
    verify_files(protocol["files"])
    matrix_path = Path(protocol["output_root"]) / "summary.json"
    matrix = json.loads(matrix_path.read_text())
    if matrix.get("protocol_sha256") != PROTOCOL_SHA or matrix.get("implementation_sha256") != protocol["implementation_sha256"]:
        raise ContractError("matrix provenance differs")
    expected = {c["case"]: c for c in protocol["cases"]}
    names = [c["case"] for c in matrix["cases"]]
    if matrix["status"] != "pass" or len(names) != len(set(names)) or set(names) != set(expected):
        raise ContractError("complete unique arm set required")
    pairs = {}
    total = 0
    for case in matrix["cases"]:
        plan = expected[case["case"]]
        if len(case["reports"]) != plan["new_runs"]:
            raise ContractError("wrong repeat count")
        reference = None
        for index, receipt in enumerate(case["reports"]):
            report_path = Path(receipt["path"])
            wanted = Path(protocol["output_root"]) / case["case"] / f"run_{index:02d}" / "report.json"
            if report_path != wanted or sha256(report_path) != receipt["sha256"]:
                raise ContractError("report binding differs")
            report = validate(report_path, protocol["implementation_sha256"])
            if report["provenance"]["settings"]["use_no_goods"] is not (plan["arm"] == "enabled"):
                raise ContractError("wrong suppression arm")
            command = [v.replace("{run_dir}", str(wanted.parent)) for v in plan["command"]]
            if json.loads((wanted.parent / "command.json").read_text()) != command:
                raise ContractError("command differs from sealed protocol")
            audit_process(json.loads((wanted.parent / "process.json").read_text()))
            if report["closure_budget"] != 24 or report["closure_calls"] > 24 or report["epochs_completed"] > 4:
                raise ContractError("search exceeded registered budget")
            current = (signature(report), feedback_signature(report), report["phases"],
                       [t["transactions"] for t in report["trials"]])
            if reference is None:
                reference = current
                first = report
            elif current != reference:
                raise ContractError("repeat behavior differs")
            total += audit_native_trials(report)
        for key in ("baseline", "final", "closure_calls", "accepted_transactions"):
            if case[key] != first[key]:
                raise ContractError("matrix row differs from search evidence")
        pairs.setdefault(plan["design"], {})[plan["arm"]] = first
    rows = []
    for design, arms in pairs.items():
        row = {"design": design, **compare_arms(arms["enabled"], arms["disabled"])}
        for arm, report in arms.items():
            row[arm] = {key: report[key] for key in
                        ("final", "closure_calls", "accepted_transactions", "stop_reason")}
        rows.append(row)
    result = {"schema": "TILEPLACE_FRONTIER_PAIRED_AUDIT_V1", "status": "pass",
              "protocol_sha256": PROTOCOL_SHA, "matrix_sha256": sha256(matrix_path),
              "verified_native_trials": total, "pairs": rows,
              "scope": "Observed development designs; suppression ablation with unchanged stopping rules"}
    for metric in ("cpd", "wirelength"):
        result[metric + "_paired_geomean_change_pct"] = 100 * (
            math.exp(sum(math.log(r[metric + "_enabled_over_disabled"]) for r in rows) / len(rows)) - 1)
    dump_json(args.output, result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
