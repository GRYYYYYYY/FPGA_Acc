#!/usr/bin/env python3
"""Build the frozen four-case TilePlace-V4 development-gate matrix."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, sha256


CASES = ("diffeq", "frisc", "elliptic", "clma")
PREREG_SHA256 = "75dce71634d613f17db59a0af923d258cf5b95fe795566a37596486656cfa3ca"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--experiments", type=Path, default=Path(__file__).parents[1] / "experiments")
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        experiments = args.experiments.resolve()
        prereg = experiments / "tileplace_v4_preregistration_2026-09-03.json"
        if sha256(prereg) != PREREG_SHA256:
            raise ContractError("TilePlace-V4 preregistration hash changed")
        rows = []
        for case in CASES:
            report_path = experiments / "tileplace_v4_dev" / case / "report.json"
            final_place = experiments / "tileplace_v4_dev" / case / "final.place"
            report = json.loads(report_path.read_text())
            if report.get("schema") != "TILEPLACE_V2_ROUTED_SEARCH_V1" or report.get("status") != "pass":
                raise ContractError(f"invalid V4 report for {case}")
            if report["preregistration"]["sha256"] != PREREG_SHA256:
                raise ContractError(f"{case} report uses a different preregistration")
            if report["output_place"]["sha256"] != sha256(final_place):
                raise ContractError(f"{case} final placement hash mismatch")
            baseline, final = report["baseline"], report["final"]
            if final.get("legal") is not True:
                raise ContractError(f"{case} final closure is not legal")
            cpd_ratio = float(final["cpd_ns"]) / float(baseline["cpd_ns"])
            wire_ratio = int(final["wirelength"]) / int(baseline["wirelength"])
            if wire_ratio > 1.005:
                raise ContractError(f"{case} violates the preregistered wirelength cap")
            rows.append(
                {
                    "case": case,
                    "baseline_cpd_ns": baseline["cpd_ns"],
                    "final_cpd_ns": final["cpd_ns"],
                    "cpd_ratio": cpd_ratio,
                    "cpd_change_pct": (cpd_ratio - 1.0) * 100.0,
                    "baseline_wirelength": baseline["wirelength"],
                    "final_wirelength": final["wirelength"],
                    "wirelength_ratio": wire_ratio,
                    "wirelength_change_pct": (wire_ratio - 1.0) * 100.0,
                    "closure_calls": report["closure_calls"],
                    "accepted_transactions": report["accepted_transactions"],
                    "report": {"path": str(report_path), "sha256": sha256(report_path)},
                    "final_place": {"path": str(final_place), "sha256": sha256(final_place)},
                }
            )
        cpd_geomean = math.exp(sum(math.log(row["cpd_ratio"]) for row in rows) / len(rows))
        wire_geomean = math.exp(sum(math.log(row["wirelength_ratio"]) for row in rows) / len(rows))
        strict = sum(row["cpd_ratio"] < 1.0 for row in rows)
        result = {
            "schema": "TILEPLACE_V4_DEVELOPMENT_MATRIX_V1",
            "status": "pass",
            "preregistration": {"path": str(prereg), "sha256": sha256(prereg)},
            "configuration": {
                "timing_weight": 2,
                "routed_timing_weight": 2,
                "congestion_weight": 1,
                "critical_distance_guard_q": 0,
                "timing_feedback_paths": 20,
            },
            "cases": rows,
            "aggregate": {
                "cases": len(rows),
                "strict_cpd_improvements": strict,
                "cpd_geomean_ratio": cpd_geomean,
                "cpd_geomean_change_pct": (cpd_geomean - 1.0) * 100.0,
                "wirelength_geomean_ratio": wire_geomean,
                "wirelength_geomean_change_pct": (wire_geomean - 1.0) * 100.0,
                "maximum_wirelength_ratio": max(row["wirelength_ratio"] for row in rows),
            },
            "development_gate": {
                "cpd_geomean_improves": cpd_geomean < 1.0,
                "all_cases_within_wirelength_cap": all(row["wirelength_ratio"] <= 1.005 for row in rows),
                "pass": cpd_geomean < 1.0 and all(row["wirelength_ratio"] <= 1.005 for row in rows),
            },
        }
        dump_json(args.output.resolve(), result)
        print(json.dumps(result["aggregate"], sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_tileplace_v4_development_matrix: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
