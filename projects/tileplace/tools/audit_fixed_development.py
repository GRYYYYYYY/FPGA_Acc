#!/usr/bin/env python3
"""Verify completed fixed-development evidence down to native trial artifacts."""

import argparse
import json
import math
from pathlib import Path

from run_fixed_development import validate
from run_v4_timing_protocol import signature, feedback_signature
from tileplace_provenance import verify_files
from tileplace_vpr import ContractError, dump_json, sha256


PROTOCOL_SHA = "7b4ef8f4c99e70435770c144b6ac0d061a33e3f0dff6f6352d42e43d44ec3396"


def audit_native_trials(report):
    count = 0
    for trial in report["trials"]:
        candidate = trial["candidate_place"]
        if sha256(Path(candidate["path"])) != candidate["sha256"]:
            raise ContractError("candidate placement hash changed")
        summary = trial["closure"]
        path = Path(summary["report_path"])
        if sha256(path) != summary["report_sha256"]:
            raise ContractError("native closure report changed")
        native = json.loads(path.read_text())
        for key in ("schema", "status", "legal", "returncode", "wirelength", "cpd_ns"):
            if native.get(key) != summary.get(key):
                raise ContractError(f"native summary mismatch: {key}")
        if native["inputs"]["golden_place"]["sha256"] != candidate["sha256"]:
            raise ContractError("native closure is bound to a different candidate")
        verify_files(list(native["outputs"].values()))
        log = Path(native["outputs"]["stdout"]["path"]).read_text()
        for marker in ("Completed placement consistency check successfully.",
                       "Completed routing consistency check successfully.",
                       "Circuit successfully routed with a channel width factor", "VPR succeeded"):
            if marker not in log:
                raise ContractError("native success marker missing")
        count += 1
    return count


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--partial", action="store_true", help="Audit only completed cases, without claiming four-case completion")
    args = parser.parse_args()
    exp = Path(__file__).resolve().parents[1] / "experiments"
    protocol_path = exp / "tileplace_fixed_development_protocol_2026-09-29.json"
    if sha256(protocol_path) != PROTOCOL_SHA:
        raise ContractError("protocol changed")
    protocol = json.loads(protocol_path.read_text())
    root = Path(protocol["output_root"])
    matrix_path = root / ("progress.json" if args.partial else "summary.json")
    matrix = json.loads(matrix_path.read_text())
    cases = matrix["completed_cases"] if args.partial else matrix["cases"]
    expected = {r["case"]: r for r in protocol["cases"]}
    names = [r["case"] for r in cases]
    if len(names) != len(set(names)) or not set(names).issubset(expected):
        raise ContractError("invalid completed case set")
    if not args.partial and set(names) != set(expected):
        raise ContractError("four-case validation incomplete")
    rows = []
    for case in cases:
        planned = expected[case["case"]]
        if len(case["reports"]) != len(planned["retained_reports"]) + planned["new_runs"]:
            raise ContractError("repeat count differs from protocol")
        reference = None
        native_count = 0
        for receipt in case["reports"]:
            path = Path(receipt["path"])
            if sha256(path) != receipt["sha256"]:
                raise ContractError("search report changed")
            report = validate(path, protocol["implementation_sha256"])
            current = (signature(report), feedback_signature(report), report["phases"],
                       [t["transactions"] for t in report["trials"]])
            if reference is None:
                reference = current
                first = report
            elif current != reference:
                raise ContractError("full repeat identity mismatch")
            native_count += audit_native_trials(report)
        cpd = first["final"]["cpd_ns"] / first["baseline"]["cpd_ns"]
        wl = first["final"]["wirelength"] / first["baseline"]["wirelength"]
        if cpd != case["cpd_ratio"] or wl != case["wirelength_ratio"]:
            raise ContractError("aggregate row disagrees with search evidence")
        rows.append({"case": case["case"], "repeats": len(case["reports"]),
                     "verified_native_trials": native_count, "cpd_change_pct": (cpd - 1) * 100,
                     "wirelength_change_pct": (wl - 1) * 100, "all_repeats_exact": True})
    result = {"schema": "TILEPLACE_FIXED_DEVELOPMENT_ARTIFACT_AUDIT_V1",
              "status": "partial" if args.partial else "pass", "protocol_sha256": PROTOCOL_SHA,
              "matrix": {"path": str(matrix_path), "sha256": sha256(matrix_path)},
              "implementation_sha256": protocol["implementation_sha256"], "cases": rows,
              "scope": "Completed development cases only; no claim about historical mixed-parser held-out evaluation"}
    if not args.partial:
        for key, ratio in (("cpd_geomean_change_pct", "cpd_ratio"), ("wirelength_geomean_change_pct", "wirelength_ratio")):
            computed = (math.exp(sum(math.log(r[ratio]) for r in cases) / len(cases)) - 1) * 100
            if abs(computed - matrix[key]) > 1e-10:
                raise ContractError("matrix geometric mean mismatch")
            result[key] = computed
    dump_json(args.output, result)
    print(json.dumps(result, sort_keys=True))


if __name__ == "__main__":
    main()
