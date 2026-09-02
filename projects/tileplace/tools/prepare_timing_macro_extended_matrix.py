#!/usr/bin/env python3
"""Audit the seven-case matrix plus the previously-probed macro-stress case."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from prepare_timing_extended_matrix import aggregate, delta, load
from tileplace_vpr import ContractError, dump_json, sha256


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.tileplace.resolve()
        experiments = root / "experiments"
        base_path = experiments / "timing_extended_matrix_2026-08-31.json"
        base = load(base_path)
        if (
            base.get("schema") != "TILEPLACE_TIMING_EXTENDED_MATRIX_V1"
            or base.get("status") != "pass"
            or len(base.get("cases", [])) != 7
        ):
            raise ContractError("seven-case matrix is not the expected passing V1 evidence")

        case_dir = experiments / "koios_conv_layer_seed1_cw300"
        endpoint_dir = experiments / "koios_conv_layer_seed1_cw300_endpoints"
        manifest_path = endpoint_dir / "manifest.json"
        cpu_path = endpoint_dir / "page2_connection_star_guard_q60000_w1.json"
        place_path = endpoint_dir / "page2_connection_star_guard_q60000_w1.place"
        repeat_path = root / "work" / "conv_layer_page2_repeat.json"
        repeat_place_path = root / "work" / "conv_layer_page2_repeat.place"
        baseline_path = case_dir / "vpr_native_closure.json"
        candidate_path = endpoint_dir / "page2_connection_star_guard_q60000_w1_vpr_native.json"
        capture_path = experiments / "conv_layer_input_capture_2026-08-31.json"
        timing_build_path = experiments / "vpr_timing_export_optional_build_2026-08-31.json"

        manifest = load(manifest_path)
        cpu = load(cpu_path)
        repeat = load(repeat_path)
        baseline = load(baseline_path)
        candidate = load(candidate_path)
        capture = load(capture_path)
        timing_build = load(timing_build_path)
        for label, evidence in (
            ("CPU", cpu),
            ("repeat", repeat),
            ("baseline closure", baseline),
            ("candidate closure", candidate),
            ("input capture", capture),
            ("timing build", timing_build),
        ):
            if evidence.get("status") != "pass" or evidence.get("legal", True) is not True:
                raise ContractError(f"conv_layer: {label} evidence is not passing")

        if cpu != repeat or sha256(place_path) != sha256(repeat_place_path):
            raise ContractError("conv_layer: CPU repeat is not byte-identical")
        if cpu["output_place_sha256"] != sha256(place_path):
            raise ContractError("conv_layer: selected placement hash differs from its report")
        if (
            cpu["page_width"] != 2
            or cpu["page_height"] != 2
            or cpu["proposal_workers"] != 1
            or cpu["critical_distance_guard_q"] != 60000
            or cpu["guarded_connections_increased"] != 0
        ):
            raise ContractError("conv_layer: frozen strategy was not preserved")

        mapping = manifest["connection_endpoint_mapping"]
        if mapping["timed_fully_mapped"] != mapping["timed_connections"]:
            raise ContractError("conv_layer: clustered endpoint mapping is incomplete")
        if mapping["atom_timing_pin_labeled"] != mapping["timed_connections"]:
            raise ContractError("conv_layer: atom timing-pin labels are incomplete")
        if mapping["atom_timing_pin_mapped"] != 16700 or mapping["atom_timing_pin_unmapped"] != 4440:
            raise ContractError("conv_layer: unexpected atom timing-pin mapping counts")
        macros = manifest["placement_macros"]
        if macros["macro_count"] != 43 or macros["member_count"] != 86:
            raise ContractError("conv_layer: native macro evidence differs")
        if capture["contract"]["sha256"] != sha256(manifest_path):
            raise ContractError("conv_layer: compact input-capture contract hash differs")
        if capture["rr_graph"]["sha256"] != manifest["inputs"]["rr_graph"]["sha256"]:
            raise ContractError("conv_layer: RR-graph hashes differ")
        if capture["connections"]["sha256"] != manifest["inputs"]["connections"]["sha256"]:
            raise ContractError("conv_layer: connection hashes differ")
        if capture["timing_export"]["output"]["sha256"] != manifest["inputs"]["timing"]["sha256"]:
            raise ContractError("conv_layer: timing hashes differ")
        if capture["timing_export_binary"]["sha256"] != timing_build["binary"]["sha256"]:
            raise ContractError("conv_layer: timing-export build provenance differs")
        if baseline["inputs"]["vpr"]["sha256"] != candidate["inputs"]["vpr"]["sha256"]:
            raise ContractError("conv_layer: baseline/candidate VPR binaries differ")
        if baseline["inputs"]["vpr"]["sha256"] != capture["frozen_correctness_binary"]["sha256"]:
            raise ContractError("conv_layer: QoR closure did not use the frozen correctness binary")
        if baseline["vpr_revision"] != candidate["vpr_revision"]:
            raise ContractError("conv_layer: baseline/candidate VPR revisions differ")
        if (baseline["wirelength"], baseline["cpd_ns"], baseline["routing_iterations"]) != (
            232357,
            5.12784,
            14,
        ):
            raise ContractError("conv_layer: same-router baseline did not reproduce frozen QoR")

        row = {
            "case": "conv_layer",
            "cohort": "macro_stress_previously_probed",
            "endpoint_mapping": mapping,
            "guarded_connections": cpu["guarded_connections"],
            "accepted_moves": cpu["accepted_moves"],
            "macros": macros,
            "internal_hpwl": [cpu["initial_wire_hpwl"], cpu["final_wire_hpwl"]],
            "internal_timing_cost_q": [cpu["initial_timing_hpwl_q"], cpu["final_timing_hpwl_q"]],
            "deterministic_output_sha256": cpu["output_place_sha256"],
            "same_router_baseline_reproduced": True,
            "baseline": {
                "routing_iterations": baseline["routing_iterations"],
                "wirelength": baseline["wirelength"],
                "cpd_ns": baseline["cpd_ns"],
            },
            "candidate": {
                "routing_iterations": candidate["routing_iterations"],
                "wirelength": candidate["wirelength"],
                "cpd_ns": candidate["cpd_ns"],
                "wirelength_delta_pct": delta(candidate["wirelength"], baseline["wirelength"]),
                "cpd_delta_pct": delta(candidate["cpd_ns"], baseline["cpd_ns"]),
            },
        }
        rows = [*base["cases"], row]
        report = {
            "schema": "TILEPLACE_TIMING_MACRO_EXTENDED_MATRIX_V1",
            "status": "pass",
            "date": "2026-08-31",
            "frozen_strategy": base["frozen_strategy"],
            "cases": rows,
            "aggregate": aggregate(rows),
            "cohort_aggregates": {
                **base["cohort_aggregates"],
                "macro_stress_previously_probed": aggregate([row]),
            },
            "endpoint_mapping": {
                key: base["endpoint_mapping"][key] + mapping[key]
                for key in (
                    "connections",
                    "mapped_sources",
                    "mapped_sinks",
                    "timed_connections",
                    "timed_fully_mapped",
                )
            },
            "atom_timing_pin_mapping": {
                "connections": base["endpoint_mapping"]["timed_connections"] + mapping["timed_connections"],
                "mapped": base["endpoint_mapping"]["timed_connections"] + mapping["atom_timing_pin_mapped"],
                "unmapped": mapping["atom_timing_pin_unmapped"],
                "strict_export_cases": 7,
                "optional_export_cases": 1,
            },
            "new_case_evidence": {
                "base_matrix": {"path": str(base_path), "sha256": sha256(base_path)},
                "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
                "cpu": {"path": str(cpu_path), "sha256": sha256(cpu_path)},
                "candidate_place": {"path": str(place_path), "sha256": sha256(place_path)},
                "baseline_closure": {"path": str(baseline_path), "sha256": sha256(baseline_path)},
                "candidate_closure": {"path": str(candidate_path), "sha256": sha256(candidate_path)},
                "input_capture": {"path": str(capture_path), "sha256": sha256(capture_path)},
                "timing_export_build": {
                    "path": str(timing_build_path),
                    "sha256": sha256(timing_build_path),
                },
            },
            "claim_boundary": (
                "conv_layer had already appeared in an earlier 4x4 macro-aware probe, so it is labeled "
                "as a previously-probed macro-stress case rather than post-freeze validation. Its final "
                "run nevertheless uses the unchanged 2x2/q60000 strategy and the same frozen correctness "
                "VPR binary/router for baseline and candidate. Unmapped atom timing pins are explicit zero-"
                "criticality rows, remain in wire cost, and are not described as timing-pin mapped."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", **report["aggregate"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_timing_macro_extended_matrix: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
