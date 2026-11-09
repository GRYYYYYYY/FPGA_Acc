#!/usr/bin/env python3
"""Audit recorded VPR subprocess times; never infer V4 end-to-end runtime."""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

from prepare_tileplace_v4_heldout_matrix import verify_search_audit
from tileplace_vpr import ContractError, dump_json, sha256


MATRIX_SHA = "744a02558869acc6baafbced927f3bf16fdd12690bcd08bce00d0accd22498cf"


def checked_json(path: Path, expected_sha: str) -> dict:
    if sha256(path) != expected_sha:
        raise ContractError(f"archived evidence hash mismatch: {path}")
    return json.loads(path.read_text())


def audit_case(row: dict) -> dict:
    report = checked_json(Path(row["report"]["path"]), row["report"]["sha256"])
    verify_search_audit(report, row["case"])
    trials = []
    for trial in report["trials"]:
        summary = trial["closure"]
        path = Path(summary["report_path"])
        closure = checked_json(path, summary["report_sha256"])
        for key in ("status", "legal", "returncode", "cpd_ns", "wirelength"):
            if closure.get(key) != summary.get(key):
                raise ContractError(f"closure summary mismatch: {path}: {key}")
        wall = closure["wall_s"]
        if isinstance(wall, bool) or not isinstance(wall, (int, float)) or not math.isfinite(wall) or wall < 0:
            raise ContractError(f"invalid subprocess wall time: {path}")
        trials.append({
            "trial": trial["trial"],
            "accepted": trial["accepted"],
            "vpr_subprocess_wall_s": wall,
            "closure_report": {"path": str(path), "sha256": summary["report_sha256"]},
        })
    accepted = sum(t["vpr_subprocess_wall_s"] for t in trials if t["accepted"])
    rejected = sum(t["vpr_subprocess_wall_s"] for t in trials if not t["accepted"])
    return {
        "case": row["case"],
        "search_report": row["report"],
        "closure_calls": len(trials),
        "accepted_closures": sum(t["accepted"] for t in trials),
        "accepted_transactions": report["accepted_transactions"],
        "accepted_vpr_subprocess_wall_s": accepted,
        "rejected_vpr_subprocess_wall_s": rejected,
        "total_vpr_subprocess_wall_s": accepted + rejected,
        "trials": trials,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--matrix", type=Path, default=Path(__file__).parents[1] / "experiments/tileplace_v4_heldout_matrix_2026-09-05.json")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    matrix = checked_json(args.matrix, MATRIX_SHA)
    cases = [audit_case(row) for row in matrix["cases"]]
    result = {
        "schema": "TILEPLACE_V4_ARCHIVED_ORACLE_COST_V1",
        "status": "pass",
        "matrix": {"path": str(args.matrix.resolve()), "sha256": MATRIX_SHA},
        "measurement_scope": "Sum of recorded time.monotonic durations around synchronous VPR subprocess.run calls in the selected frozen search traces",
        "excluded": ["baseline/input preparation", "Python proposal search", "feedback refresh", "closure-driver validation and hashing", "output serialization", "earlier interrupted or infrastructure-retry traces"],
        "limitations": ["Archived single-run observations, not controlled repeated performance measurements", "Not V4 end-to-end time, not total historical experiment cost, and not a speedup", "No equal-time search comparator"],
        "cases": cases,
    }
    dump_json(args.output.resolve(), result)
    for row in cases:
        print(f"{row['case']}: {row['closure_calls']} calls, {row['total_vpr_subprocess_wall_s']:.3f} s VPR subprocess sum, {row['rejected_vpr_subprocess_wall_s']:.3f} s rejected")


if __name__ == "__main__":
    main()
