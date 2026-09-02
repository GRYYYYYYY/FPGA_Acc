#!/usr/bin/env python3
"""Audit the frozen four-case connection-timing guard matrix."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, sha256


CASES = (
    ("diffeq", "diffeq_seed1_cw200", "development"),
    ("frisc", "frisc_seed1_cw200", "development"),
    ("elliptic", "elliptic_seed1_cw200", "development"),
    ("clma", "clma_seed1_cw200", "development"),
    ("spmv", "spmv_seed1_cw300", "post_freeze_validation"),
    ("softmax", "softmax_seed1_cw300", "post_freeze_validation"),
)


def load(path: Path) -> dict:
    if not path.is_file():
        raise ContractError(f"missing evidence: {path}")
    return json.loads(path.read_text())


def delta(candidate: float, baseline: float) -> float:
    return (candidate / baseline - 1.0) * 100.0


def geomean_delta(rows: list[dict], key: str) -> float:
    return (math.exp(sum(math.log(row["candidate"][key] / row["baseline"][key]) for row in rows) / len(rows)) - 1.0) * 100.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.tileplace.resolve()
        experiments = root / "experiments"
        selected_rows = []
        wire0_rows = []
        for short_name, directory_name, cohort in CASES:
            base_dir = experiments / directory_name
            endpoint_dir = experiments / f"{directory_name}_endpoints"
            baseline = load(base_dir / "vpr_native_closure.json")
            manifest = load(endpoint_dir / "manifest.json")
            selected_cpu = load(endpoint_dir / "page2_connection_star_guard_q60000_w1.json")
            selected_native_path = (
                endpoint_dir / "page2_connection_star_guard_q60000_w1_vpr_native.json"
            )
            selected_native_reused_from_page4 = False
            if selected_native_path.is_file():
                selected_native = load(selected_native_path)
            else:
                page4_cpu = load(endpoint_dir / "page4_connection_star_guard_q60000_w1.json")
                if selected_cpu["output_place_sha256"] != page4_cpu["output_place_sha256"]:
                    raise ContractError(f"{short_name}: page2 unique placement lacks native closure")
                selected_native = load(
                    endpoint_dir / "page4_connection_star_guard_q60000_w1_vpr_native.json"
                )
                selected_native_reused_from_page4 = True
            repeat_name = f"{directory_name}_page2_q60000_repeat.json"
            repeat = load(root / "work" / repeat_name)
            evidence_set = [baseline, selected_cpu, selected_native, repeat]
            if cohort == "development":
                wire0_cpu = load(
                    endpoint_dir / "page4_connection_star_guard_q60000_wire0_w1.json"
                )
                wire0_native = load(
                    endpoint_dir / "page4_connection_star_guard_q60000_wire0_w1_vpr_native.json"
                )
                evidence_set.extend((wire0_cpu, wire0_native))
            for evidence in evidence_set:
                if evidence.get("status") != "pass" or evidence.get("legal", True) is not True:
                    raise ContractError(f"{short_name}: non-passing evidence")
            mapping = manifest["connection_endpoint_mapping"]
            if mapping["timed_fully_mapped"] != mapping["timed_connections"]:
                raise ContractError(f"{short_name}: incomplete endpoint mapping")
            if selected_cpu["critical_distance_guard_q"] != 60000:
                raise ContractError(f"{short_name}: selected threshold is not q60000")
            if selected_cpu["guarded_connections_increased"] != 0:
                raise ContractError(f"{short_name}: protected connection distance increased")
            selected_place = endpoint_dir / "page2_connection_star_guard_q60000_w1.place"
            selected_hash = selected_cpu["output_place_sha256"]
            if sha256(selected_place) != selected_hash or repeat["output_place_sha256"] != selected_hash:
                raise ContractError(f"{short_name}: deterministic placement evidence differs")

            baseline_metrics = {
                "routing_iterations": baseline["routing_iterations"],
                "wirelength": baseline["wirelength"],
                "cpd_ns": baseline["cpd_ns"],
            }
            selected_metrics = {
                "routing_iterations": selected_native["routing_iterations"],
                "wirelength": selected_native["wirelength"],
                "cpd_ns": selected_native["cpd_ns"],
                "wirelength_delta_pct": delta(selected_native["wirelength"], baseline["wirelength"]),
                "cpd_delta_pct": delta(selected_native["cpd_ns"], baseline["cpd_ns"]),
            }
            selected_rows.append(
                {
                    "case": short_name,
                    "cohort": cohort,
                    "endpoint_mapping": mapping,
                    "guarded_connections": selected_cpu["guarded_connections"],
                    "accepted_moves": selected_cpu["accepted_moves"],
                    "internal_hpwl": [selected_cpu["initial_wire_hpwl"], selected_cpu["final_wire_hpwl"]],
                    "internal_timing_cost_q": [
                        selected_cpu["initial_timing_hpwl_q"], selected_cpu["final_timing_hpwl_q"]
                    ],
                    "deterministic_output_sha256": selected_hash,
                    "native_evidence_reused_from_page4_by_hash": selected_native_reused_from_page4,
                    "baseline": baseline_metrics,
                    "candidate": selected_metrics,
                }
            )
            if cohort == "development":
                wire0_metrics = {
                    "routing_iterations": wire0_native["routing_iterations"],
                    "wirelength": wire0_native["wirelength"],
                    "cpd_ns": wire0_native["cpd_ns"],
                    "wirelength_delta_pct": delta(wire0_native["wirelength"], baseline["wirelength"]),
                    "cpd_delta_pct": delta(wire0_native["cpd_ns"], baseline["cpd_ns"]),
                }
                wire0_rows.append(
                    {
                        "case": short_name,
                        "baseline": baseline_metrics,
                        "candidate": wire0_metrics,
                        "placement_sha256": wire0_cpu["output_place_sha256"],
                    }
                )

        def aggregate(rows: list[dict]) -> dict:
            return {
                "cases": len(rows),
                "wirelength_geomean_delta_pct": geomean_delta(rows, "wirelength"),
                "cpd_geomean_delta_pct": geomean_delta(rows, "cpd_ns"),
                "wirelength_worst_delta_pct": max(row["candidate"]["wirelength_delta_pct"] for row in rows),
                "cpd_worst_delta_pct": max(row["candidate"]["cpd_delta_pct"] for row in rows),
                "wirelength_improved_cases": sum(row["candidate"]["wirelength_delta_pct"] < 0 for row in rows),
                "cpd_nonregressing_cases": sum(row["candidate"]["cpd_delta_pct"] <= 0 for row in rows),
            }

        report = {
            "schema": "TILEPLACE_TIMING_MULTICASE_MATRIX_V2",
            "status": "pass",
            "date": "2026-08-31",
            "frozen_strategy": {
                "page_size": [2, 2],
                "timing_model": "connection_star",
                "timing_weight": 1,
                "wire_weight": 256,
                "critical_distance_guard_q": 60000,
                "critical_distance_slack": 0,
                "per_transaction_hpwl_cap": None,
            },
            "cases": selected_rows,
            "aggregate": aggregate(selected_rows),
            "cohort_aggregates": {
                cohort: aggregate([row for row in selected_rows if row["cohort"] == cohort])
                for cohort in ("development", "post_freeze_validation")
            },
            "wire0_ablation": {
                "description": "four-case development ablation: prior 4x4 strategy plus a non-increasing touched-net HPWL transaction cap",
                "page_size": [4, 4],
                "cases": wire0_rows,
                "aggregate": aggregate(wire0_rows),
                "decision": "reject_as_default",
            },
            "claim_boundary": (
                "This matrix is deterministic CPU placement plus serial VPR route/analysis on six academic "
                "cases, including two cases first evaluated after the strategy was frozen. It is not hardware "
                "performance evidence. The frozen strategy improves geometric-mean "
                "wirelength and CPD, but per-case routed wirelength is not monotonic and the worst case is "
                "reported explicitly."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", **report["aggregate"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_timing_multicase_matrix: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
