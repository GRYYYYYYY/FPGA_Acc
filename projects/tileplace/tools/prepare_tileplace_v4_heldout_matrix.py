#!/usr/bin/env python3
"""Build the frozen six-case TilePlace-V4 held-out publication-gate matrix."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, location, parse_place, sha256


PREREG_SHA256 = "75dce71634d613f17db59a0af923d258cf5b95fe795566a37596486656cfa3ca"
REPORTS = {
    "pdc": "report.json",
    "dsip": "report.json",
    "bnn": "report_retry1.json",
    "gemm_layer": "report_retry1.json",
    "tdarknet_like.small": "report_retry1.json",
    "ucsb_152_tap_fir": "report_retry1.json",
}

FROZEN_CONFIG = {
    "candidate_limit": 64,
    "chain_candidate_limit": 16,
    "congestion_weight": 1,
    "critical_distance_guard_q": 0,
    "critical_distance_slack": 0,
    "page_height": 2,
    "page_width": 2,
    "routed_timing_weight": 2,
    "timing_weight": 2,
}
FROZEN_CLOSURE_BUDGET = 24


def verify_search_audit(report: dict, case: str) -> None:
    """Verify that the compact final state is justified by the trial trace."""
    trials = report.get("trials")
    closure_calls = report.get("closure_calls")
    if not isinstance(trials, list) or len(trials) != closure_calls:
        raise ContractError(f"{case} trial trace does not match its closure count")
    if [trial.get("trial") for trial in trials] != list(range(1, closure_calls + 1)):
        raise ContractError(f"{case} trial numbering is not contiguous")
    incumbent = report.get("baseline")
    for trial in trials:
        if trial.get("incumbent_before") != incumbent:
            raise ContractError(f"{case} trial {trial['trial']} breaks the incumbent state chain")
        if type(trial.get("accepted")) is not bool:
            raise ContractError(f"{case} trial {trial['trial']} has no boolean decision")
        if trial["accepted"]:
            incumbent = trial.get("closure")
    if incumbent != report.get("final"):
        raise ContractError(f"{case} final metrics do not match the replayed incumbent")
    accepted = [trial for trial in trials if trial.get("accepted") is True]
    accepted_count = sum(int(trial.get("transaction_count", -1)) for trial in accepted)
    if accepted_count != report.get("accepted_transactions"):
        raise ContractError(f"{case} accepted transaction count does not match its trial trace")

    output_sha = report.get("output_place", {}).get("sha256")
    if accepted:
        last = accepted[-1]
        if last.get("candidate_place", {}).get("sha256") != output_sha:
            raise ContractError(f"{case} final placement is not the last accepted candidate")
        if last.get("closure") != report.get("final"):
            raise ContractError(f"{case} final metrics do not match the last accepted closure")
    else:
        input_path = Path(report.get("input_place", {}).get("path", ""))
        output_path = Path(report.get("output_place", {}).get("path", ""))
        _input_header, input_rows = parse_place(input_path)
        _output_header, output_rows = parse_place(output_path)
        input_state = {row["name"]: location(row) for row in input_rows}
        output_state = {row["name"]: location(row) for row in output_rows}
        if input_state != output_state:
            raise ContractError(f"{case} zero-acceptance run changed the input placement")
        if report.get("baseline") != report.get("final"):
            raise ContractError(f"{case} zero-acceptance run changed the baseline metrics")


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
        for case, filename in REPORTS.items():
            result_dir = experiments / "tileplace_v4_heldout" / case
            report_path = result_dir / filename
            report = json.loads(report_path.read_text())
            if report.get("schema") != "TILEPLACE_V2_ROUTED_SEARCH_V1" or report.get("status") != "pass":
                raise ContractError(f"invalid V4 report for {case}")
            if report["preregistration"]["sha256"] != PREREG_SHA256:
                raise ContractError(f"{case} report uses a different preregistration")
            if report.get("config") != FROZEN_CONFIG:
                raise ContractError(f"{case} report does not use the frozen V4 configuration")
            if report.get("closure_budget") != FROZEN_CLOSURE_BUDGET:
                raise ContractError(f"{case} report does not use the frozen V4 closure budget")
            closure_calls = report.get("closure_calls")
            if not isinstance(closure_calls, int) or not 0 <= closure_calls <= FROZEN_CLOSURE_BUDGET:
                raise ContractError(f"{case} report has an invalid closure count")
            verify_search_audit(report, case)
            final_place = Path(report["output_place"]["path"])
            if report["output_place"]["sha256"] != sha256(final_place):
                raise ContractError(f"{case} final placement hash mismatch")
            baseline, final = report["baseline"], report["final"]
            if baseline.get("legal") is not True or final.get("legal") is not True:
                raise ContractError(f"{case} baseline or final closure is not legal")
            cpd_ratio = float(final["cpd_ns"]) / float(baseline["cpd_ns"])
            wire_ratio = int(final["wirelength"]) / int(baseline["wirelength"])
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
                    "closure_calls": closure_calls,
                    "accepted_transactions": report["accepted_transactions"],
                    "report": {"path": str(report_path), "sha256": sha256(report_path)},
                    "final_place": {"path": str(final_place), "sha256": sha256(final_place)},
                }
            )
        cpd_geomean = math.exp(sum(math.log(row["cpd_ratio"]) for row in rows) / len(rows))
        wire_geomean = math.exp(sum(math.log(row["wirelength_ratio"]) for row in rows) / len(rows))
        strict = sum(row["cpd_ratio"] < 1.0 for row in rows)
        gate = {
            "all_six_native_legal": len(rows) == 6,
            "cpd_geomean_ratio_at_most_0_99": cpd_geomean <= 0.99,
            "at_least_three_strict_cpd_improvements": strict >= 3,
            "wirelength_geomean_ratio_at_most_1_0025": wire_geomean <= 1.0025,
            "all_cases_wirelength_ratio_at_most_1_005": all(
                row["wirelength_ratio"] <= 1.005 for row in rows
            ),
        }
        gate["pass"] = all(gate.values())
        result = {
            "schema": "TILEPLACE_V4_HELDOUT_MATRIX_V1",
            "status": "pass",
            "preregistration": {"path": str(prereg), "sha256": sha256(prereg)},
            "audit": {
                "frozen_configuration_verified": True,
                "frozen_closure_budget": FROZEN_CLOSURE_BUDGET,
                "all_reports_within_closure_budget": True,
                "all_trial_state_chains_verified": True,
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
            "publication_gate": gate,
        }
        dump_json(args.output.resolve(), result)
        print(json.dumps({"aggregate": result["aggregate"], "publication_gate": gate}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_tileplace_v4_heldout_matrix: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
