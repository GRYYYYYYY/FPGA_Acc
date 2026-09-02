#!/usr/bin/env python3
"""Audit the frozen six-case matrix plus the post-freeze attention-layer case."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, sha256


def load(path: Path) -> dict:
    if not path.is_file():
        raise ContractError(f"missing evidence: {path}")
    return json.loads(path.read_text())


def delta(candidate: float, baseline: float) -> float:
    return (candidate / baseline - 1.0) * 100.0


def aggregate(rows: list[dict]) -> dict:
    def geomean(key: str) -> float:
        return (
            math.exp(
                sum(math.log(row["candidate"][key] / row["baseline"][key]) for row in rows)
                / len(rows)
            )
            - 1.0
        ) * 100.0

    return {
        "cases": len(rows),
        "wirelength_geomean_delta_pct": geomean("wirelength"),
        "cpd_geomean_delta_pct": geomean("cpd_ns"),
        "wirelength_worst_delta_pct": max(
            row["candidate"]["wirelength_delta_pct"] for row in rows
        ),
        "cpd_worst_delta_pct": max(row["candidate"]["cpd_delta_pct"] for row in rows),
        "wirelength_improved_cases": sum(
            row["candidate"]["wirelength_delta_pct"] < 0 for row in rows
        ),
        "cpd_nonregressing_cases": sum(
            row["candidate"]["cpd_delta_pct"] <= 0 for row in rows
        ),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.tileplace.resolve()
        experiments = root / "experiments"
        base_path = experiments / "timing_multicase_matrix_2026-08-31.json"
        base = load(base_path)
        if (
            base.get("schema") != "TILEPLACE_TIMING_MULTICASE_MATRIX_V2"
            or base.get("status") != "pass"
            or len(base.get("cases", [])) != 6
        ):
            raise ContractError("frozen six-case matrix is not the expected passing V2 evidence")

        case_dir = experiments / "attention_layer_seed1_cw300"
        endpoint_dir = experiments / "attention_layer_seed1_cw300_endpoints"
        manifest = load(endpoint_dir / "manifest.json")
        cpu_path = endpoint_dir / "page2_connection_star_guard_q60000_w1.json"
        place_path = endpoint_dir / "page2_connection_star_guard_q60000_w1.place"
        cpu = load(cpu_path)
        repeat_path = root / "work" / "attention_layer_repeat.json"
        repeat_place_path = root / "work" / "attention_layer_repeat.place"
        repeat = load(repeat_path)
        baseline = load(case_dir / "vpr_native_closure.json")
        candidate = load(endpoint_dir / "page2_connection_star_guard_q60000_w1_vpr_native.json")
        macro_capture = load(case_dir / "vpr_macro_capture.json")
        timing_build = load(experiments / "vpr_timing_export_build_2026-08-31.json")
        input_capture_path = experiments / "attention_layer_input_capture_2026-08-31.json"
        input_capture = load(input_capture_path)

        for label, evidence in (
            ("CPU", cpu),
            ("repeat", repeat),
            ("baseline closure", baseline),
            ("candidate closure", candidate),
            ("macro capture", macro_capture),
            ("timing build", timing_build),
            ("input capture", input_capture),
        ):
            if evidence.get("status") != "pass" or evidence.get("legal", True) is not True:
                raise ContractError(f"attention_layer: {label} evidence is not passing")
        if cpu != repeat or sha256(place_path) != sha256(repeat_place_path):
            raise ContractError("attention_layer: CPU repeat is not byte-identical")
        if cpu["output_place_sha256"] != sha256(place_path):
            raise ContractError("attention_layer: selected placement hash differs from its report")
        if cpu["critical_distance_guard_q"] != 60000 or cpu["guarded_connections_increased"] != 0:
            raise ContractError("attention_layer: frozen critical-distance guard was not preserved")
        if cpu["page_width"] != 2 or cpu["page_height"] != 2 or cpu["proposal_workers"] != 1:
            raise ContractError("attention_layer: frozen page/worker configuration differs")

        mapping = manifest["connection_endpoint_mapping"]
        if mapping["timed_fully_mapped"] != mapping["timed_connections"]:
            raise ContractError("attention_layer: incomplete endpoint mapping")
        macros = manifest["placement_macros"]
        if macros != macro_capture["macros"] or macros["macro_count"] != 4:
            raise ContractError("attention_layer: native macro evidence differs")
        if macro_capture["inputs"]["rr_graph"]["sha256"] != manifest["inputs"]["rr_graph"]["sha256"]:
            raise ContractError("attention_layer: RR-graph hashes differ between capture and contract")
        if input_capture["rr_graph"]["sha256"] != manifest["inputs"]["rr_graph"]["sha256"]:
            raise ContractError("attention_layer: compact input-capture RR-graph hash differs")
        if input_capture["connections"]["sha256"] != manifest["inputs"]["connections"]["sha256"]:
            raise ContractError("attention_layer: compact input-capture connection hash differs")
        if input_capture["timing_export"]["output"]["sha256"] != manifest["inputs"]["timing"]["sha256"]:
            raise ContractError("attention_layer: compact input-capture timing hash differs")
        if input_capture["contract"]["timed_fully_mapped"] != mapping["timed_fully_mapped"]:
            raise ContractError("attention_layer: compact input-capture mapping count differs")
        if input_capture["binaries"]["timing_export"]["sha256"] != timing_build["binary"]["sha256"]:
            raise ContractError("attention_layer: timing-export binary provenance differs")
        if timing_build["frozen_correctness_binary"]["sha256_after_build"] != baseline["inputs"]["vpr"]["sha256"]:
            raise ContractError("attention_layer: baseline closure did not use the frozen VPR binary")
        if baseline["inputs"]["vpr"]["sha256"] != candidate["inputs"]["vpr"]["sha256"]:
            raise ContractError("attention_layer: baseline and candidate VPR binaries differ")
        if baseline["vpr_revision"] != candidate["vpr_revision"]:
            raise ContractError("attention_layer: baseline and candidate VPR revisions differ")
        if baseline["wirelength"] != 544069 or baseline["cpd_ns"] != 8.82262:
            raise ContractError("attention_layer: local same-router baseline did not reproduce frozen QoR")

        baseline_metrics = {
            "routing_iterations": baseline["routing_iterations"],
            "wirelength": baseline["wirelength"],
            "cpd_ns": baseline["cpd_ns"],
        }
        candidate_metrics = {
            "routing_iterations": candidate["routing_iterations"],
            "wirelength": candidate["wirelength"],
            "cpd_ns": candidate["cpd_ns"],
            "wirelength_delta_pct": delta(candidate["wirelength"], baseline["wirelength"]),
            "cpd_delta_pct": delta(candidate["cpd_ns"], baseline["cpd_ns"]),
        }
        attention_row = {
            "case": "attention_layer",
            "cohort": "post_freeze_validation",
            "endpoint_mapping": mapping,
            "guarded_connections": cpu["guarded_connections"],
            "accepted_moves": cpu["accepted_moves"],
            "macros": macros,
            "internal_hpwl": [cpu["initial_wire_hpwl"], cpu["final_wire_hpwl"]],
            "internal_timing_cost_q": [
                cpu["initial_timing_hpwl_q"],
                cpu["final_timing_hpwl_q"],
            ],
            "deterministic_output_sha256": cpu["output_place_sha256"],
            "same_router_baseline_reproduced": True,
            "baseline": baseline_metrics,
            "candidate": candidate_metrics,
        }
        rows = [*base["cases"], attention_row]
        post_freeze = [row for row in rows if row["cohort"] == "post_freeze_validation"]
        total_mapping = {
            key: sum(row["endpoint_mapping"][key] for row in rows)
            for key in (
                "connections",
                "mapped_sources",
                "mapped_sinks",
                "timed_connections",
                "timed_fully_mapped",
            )
        }
        report = {
            "schema": "TILEPLACE_TIMING_EXTENDED_MATRIX_V1",
            "status": "pass",
            "date": "2026-08-31",
            "frozen_strategy": base["frozen_strategy"],
            "cases": rows,
            "aggregate": aggregate(rows),
            "cohort_aggregates": {
                "development": aggregate([row for row in rows if row["cohort"] == "development"]),
                "post_freeze_validation": aggregate(post_freeze),
            },
            "endpoint_mapping": total_mapping,
            "new_case_evidence": {
                "base_matrix": {"path": str(base_path), "sha256": sha256(base_path)},
                "cpu": {"path": str(cpu_path), "sha256": sha256(cpu_path)},
                "candidate_place": {"path": str(place_path), "sha256": sha256(place_path)},
                "baseline_closure": {
                    "path": str(case_dir / "vpr_native_closure.json"),
                    "sha256": sha256(case_dir / "vpr_native_closure.json"),
                },
                "candidate_closure": {
                    "path": str(endpoint_dir / "page2_connection_star_guard_q60000_w1_vpr_native.json"),
                    "sha256": sha256(endpoint_dir / "page2_connection_star_guard_q60000_w1_vpr_native.json"),
                },
                "macro_capture": {
                    "path": str(case_dir / "vpr_macro_capture.json"),
                    "sha256": sha256(case_dir / "vpr_macro_capture.json"),
                },
                "timing_export_build": {
                    "path": str(experiments / "vpr_timing_export_build_2026-08-31.json"),
                    "sha256": sha256(experiments / "vpr_timing_export_build_2026-08-31.json"),
                },
                "input_capture": {
                    "path": str(input_capture_path),
                    "sha256": sha256(input_capture_path),
                },
            },
            "wire0_ablation": base["wire0_ablation"],
            "claim_boundary": (
                "This post-freeze extension adds attention_layer without changing the frozen 2x2/q60000 "
                "strategy. All seven cases use deterministic CPU refinement and serial VPR route/analysis; "
                "the attention-layer baseline was reproduced with the same VPR binary and router as its "
                "candidate. This is CPU/VPR QoR evidence, not hardware performance."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", **report["aggregate"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_timing_extended_matrix: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
