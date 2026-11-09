#!/usr/bin/env python3
"""Audit the nine-case matrix plus preregistered Titan23 stereo_vision."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from prepare_timing_extended_matrix import aggregate, delta, load
from tileplace_vpr import ContractError, dump_json, sha256


def require_option(command: list[str], option: str, expected: str) -> None:
    if option not in command:
        raise ContractError(f"stereo closure omits {option}")
    index = command.index(option)
    if index + 1 >= len(command) or command[index + 1] != expected:
        raise ContractError(f"stereo closure has unexpected {option}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.tileplace.resolve()
        experiments = root / "experiments"
        base_path = experiments / "timing_titan_extended_matrix_2026-09-01.json"
        base = load(base_path)
        if base.get("status") != "pass" or len(base.get("cases", [])) != 9:
            raise ContractError("nine-case matrix is not the frozen passing evidence")

        case_dir = experiments / "titan23_stereo_vision_seed3_cw300"
        endpoint_dir = experiments / "titan23_stereo_vision_seed3_cw300_endpoints"
        manifest_path = endpoint_dir / "manifest.json"
        cpu_path = endpoint_dir / "page2_connection_star_guard_q60000_w1.json"
        place_path = endpoint_dir / "page2_connection_star_guard_q60000_w1.place"
        repeat_dir = root / "work" / "titan23_stereo_vision_page2_repeat"
        repeat_path = repeat_dir / "page2_connection_star_guard_q60000_w1.json"
        repeat_place = repeat_dir / "page2_connection_star_guard_q60000_w1.place"
        baseline_path = case_dir / "vpr_native_closure.json"
        candidate_path = endpoint_dir / "page2_connection_star_guard_q60000_w1_vpr_native.json"
        macro_path = case_dir / "vpr_macro_capture.json"
        capture_path = experiments / "titan23_stereo_vision_input_capture_2026-09-02.json"
        prereg_path = experiments / "titan23_stereo_vision_preregistration_2026-09-01.json"

        manifest, cpu, repeat = load(manifest_path), load(cpu_path), load(repeat_path)
        baseline, candidate = load(baseline_path), load(candidate_path)
        macro, capture, prereg = load(macro_path), load(capture_path), load(prereg_path)
        for label, evidence in (
            ("CPU", cpu), ("repeat", repeat), ("baseline", baseline),
            ("candidate", candidate), ("macro", macro), ("capture", capture),
        ):
            if evidence.get("status") != "pass" or evidence.get("legal", True) is not True:
                raise ContractError(f"stereo {label} evidence is not passing")
        if prereg.get("status") != "preregistered_before_input_capture_or_tileplace_run":
            raise ContractError("stereo preregistration is invalid")

        if cpu != repeat or sha256(place_path) != sha256(repeat_place):
            raise ContractError("stereo CPU repeat is not byte-identical")
        if cpu["output_place_sha256"] != sha256(place_path):
            raise ContractError("stereo selected placement hash differs from report")
        if not (
            cpu["page_width"] == cpu["page_height"] == 2
            and cpu["passes"][-1]["pass"] == 7
            and cpu["candidate_limit"] == 64
            and cpu["proposal_workers"] == 1
            and cpu["wire_weight"] == 256
            and cpu["timing_weight"] == 1
            and cpu["timing_model"] == "connection_star"
            and cpu["critical_distance_guard_q"] == 60000
            and cpu["critical_distance_slack"] == 0
            and cpu["guarded_connections_increased"] == 0
        ):
            raise ContractError("stereo frozen strategy was not preserved")

        mapping = manifest["connection_endpoint_mapping"]
        expected_mapping = {
            "connections": 81610,
            "mapped_sources": 81610,
            "mapped_sinks": 81610,
            "timed_connections": 81610,
            "timed_fully_mapped": 81610,
            "atom_timing_pin_labeled": 81610,
            "atom_timing_pin_mapped": 81499,
            "atom_timing_pin_unmapped": 111,
        }
        if mapping != expected_mapping:
            raise ContractError("stereo endpoint mapping accounting differs")
        macros = manifest["placement_macros"]
        if macros != macro["macros"] or macros["macro_count"] != 150 or macros["member_count"] != 300:
            raise ContractError("stereo native macro evidence differs")
        if capture["contract"]["sha256"] != sha256(manifest_path):
            raise ContractError("stereo capture contract hash differs")
        if baseline["inputs"]["vpr"]["sha256"] != candidate["inputs"]["vpr"]["sha256"]:
            raise ContractError("stereo baseline/candidate binaries differ")
        if baseline["inputs"]["vpr"]["sha256"] != capture["frozen_correctness_binary"]["sha256"]:
            raise ContractError("stereo closure did not use frozen correctness VPR")
        if (baseline["wirelength"], baseline["cpd_ns"], baseline["routing_iterations"]) != (592827, 7.51746, 15):
            raise ContractError("stereo baseline did not reproduce preregistered QoR")

        sdc_path = capture["source_inputs"]["sdc"]["path"]
        for closure in (baseline, candidate):
            for option, expected in (
                ("--sdc_file", sdc_path), ("--router_lookahead", "map"),
                ("--initial_pres_fac", "1.0"), ("--router_profiler_astar_fac", "1.5"),
                ("--max_router_iterations", "400"),
            ):
                require_option(closure["command"], option, expected)

        row = {
            "case": "titan23_stereo_vision",
            "cohort": "post_freeze_validation",
            "architecture_family": "Titan23 Stratix IV",
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
            "schema": "TILEPLACE_TIMING_TITAN_STEREO_EXTENDED_MATRIX_V1",
            "status": "pass",
            "date": "2026-09-02",
            "frozen_strategy": base["frozen_strategy"],
            "cases": rows,
            "aggregate": aggregate(rows),
            "cohort_aggregates": {
                name: aggregate([item for item in rows if item["cohort"] == name])
                for name in sorted({item["cohort"] for item in rows})
            },
            "architecture_aggregates": {
                "COFFE_22nm": aggregate(rows[:8]),
                "Titan23_Stratix_IV": aggregate(rows[8:]),
            },
            "endpoint_mapping": {
                key: base["endpoint_mapping"][key] + mapping[key]
                for key in ("connections", "mapped_sources", "mapped_sinks", "timed_connections", "timed_fully_mapped")
            },
            "atom_timing_pin_mapping": {
                "connections": base["atom_timing_pin_mapping"]["connections"] + mapping["timed_connections"],
                "mapped": base["atom_timing_pin_mapping"]["mapped"] + mapping["atom_timing_pin_mapped"],
                "unmapped": base["atom_timing_pin_mapping"]["unmapped"] + mapping["atom_timing_pin_unmapped"],
                "strict_export_cases": base["atom_timing_pin_mapping"]["strict_export_cases"],
                "optional_export_cases": base["atom_timing_pin_mapping"]["optional_export_cases"] + 1,
            },
            "new_case_evidence": {
                name: {"path": str(path), "sha256": sha256(path)}
                for name, path in {
                    "base_matrix": base_path, "preregistration": prereg_path,
                    "input_capture": capture_path, "manifest": manifest_path,
                    "cpu": cpu_path, "candidate_place": place_path,
                    "baseline_closure": baseline_path, "candidate_closure": candidate_path,
                    "macro_capture": macro_path,
                }.items()
            },
            "claim_boundary": (
                "stereo_vision is the outcome-blind preregistered second Titan23 point. It uses exact "
                "Titan 2.0.0 input hashes and the unchanged frozen strategy/router. Its routed-wirelength "
                "regression is retained, and 111 atom-pin-unmapped connections are explicitly labeled."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", **report["aggregate"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_timing_titan_stereo_extended_matrix: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
