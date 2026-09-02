#!/usr/bin/env python3
"""Audit the eight-case matrix plus post-freeze Titan23 neuron."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from prepare_timing_extended_matrix import aggregate, delta, load
from tileplace_vpr import ContractError, dump_json, sha256


def require_option(command: list[str], option: str, expected: str) -> None:
    try:
        index = command.index(option)
    except ValueError as error:
        raise ContractError(f"Titan closure command omits {option}") from error
    if index + 1 >= len(command) or command[index + 1] != expected:
        raise ContractError(
            f"Titan closure command has {option}={command[index + 1]!r}, expected {expected!r}"
        )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.tileplace.resolve()
        workspace = root.parents[1]
        experiments = root / "experiments"
        base_path = experiments / "timing_macro_extended_matrix_2026-08-31.json"
        base = load(base_path)
        if (
            base.get("schema") != "TILEPLACE_TIMING_MACRO_EXTENDED_MATRIX_V1"
            or base.get("status") != "pass"
            or len(base.get("cases", [])) != 8
        ):
            raise ContractError("eight-case matrix is not the expected passing V1 evidence")

        case_dir = experiments / "titan23_neuron_seed3_cw300"
        endpoint_dir = experiments / "titan23_neuron_seed3_cw300_endpoints"
        manifest_path = endpoint_dir / "manifest.json"
        cpu_path = endpoint_dir / "page2_connection_star_guard_q60000_w1.json"
        place_path = endpoint_dir / "page2_connection_star_guard_q60000_w1.place"
        repeat_path = root / "work" / "titan23_neuron_page2_repeat.json"
        repeat_place_path = root / "work" / "titan23_neuron_page2_repeat.place"
        baseline_path = case_dir / "vpr_native_closure.json"
        candidate_path = endpoint_dir / "page2_connection_star_guard_q60000_w1_vpr_native.json"
        macro_path = case_dir / "vpr_macro_capture.json"
        capture_path = experiments / "titan23_neuron_input_capture_2026-09-01.json"
        timing_build_path = experiments / "vpr_timing_export_optional_build_2026-08-31.json"

        manifest = load(manifest_path)
        cpu = load(cpu_path)
        repeat = load(repeat_path)
        baseline = load(baseline_path)
        candidate = load(candidate_path)
        macro = load(macro_path)
        capture = load(capture_path)
        timing_build = load(timing_build_path)
        for label, evidence in (
            ("CPU", cpu),
            ("repeat", repeat),
            ("baseline closure", baseline),
            ("candidate closure", candidate),
            ("macro capture", macro),
            ("input capture", capture),
            ("timing build", timing_build),
        ):
            if evidence.get("status") != "pass" or evidence.get("legal", True) is not True:
                raise ContractError(f"Titan neuron: {label} evidence is not passing")

        if cpu != repeat or sha256(place_path) != sha256(repeat_place_path):
            raise ContractError("Titan neuron: CPU repeat is not byte-identical")
        if cpu["output_place_sha256"] != sha256(place_path):
            raise ContractError("Titan neuron: selected placement hash differs from its report")
        if (
            cpu["page_width"] != 2
            or cpu["page_height"] != 2
            or cpu["passes"][-1]["pass"] != 7
            or cpu["candidate_limit"] != 64
            or cpu["proposal_workers"] != 1
            or cpu["wire_weight"] != 256
            or cpu["timing_weight"] != 1
            or cpu["critical_distance_guard_q"] != 60000
            or cpu["critical_distance_slack"] != 0
            or cpu["guarded_connections_increased"] != 0
        ):
            raise ContractError("Titan neuron: frozen strategy was not preserved")

        mapping = manifest["connection_endpoint_mapping"]
        if mapping["timed_fully_mapped"] != mapping["timed_connections"]:
            raise ContractError("Titan neuron: clustered endpoint mapping is incomplete")
        if mapping["atom_timing_pin_mapped"] != mapping["timed_connections"]:
            raise ContractError("Titan neuron: atom timing-pin mapping is incomplete")
        if mapping["atom_timing_pin_unmapped"] != 0 or mapping["timed_connections"] != 77106:
            raise ContractError("Titan neuron: unexpected timing mapping counts")
        macros = manifest["placement_macros"]
        if macros != macro["macros"] or macros["macro_count"] != 101:
            raise ContractError("Titan neuron: native macro evidence differs")
        if capture["contract"]["sha256"] != sha256(manifest_path):
            raise ContractError("Titan neuron: compact input-capture contract hash differs")
        if capture["rr_graph"]["sha256"] != manifest["inputs"]["rr_graph"]["sha256"]:
            raise ContractError("Titan neuron: RR-graph hashes differ")
        if capture["connections"]["sha256"] != manifest["inputs"]["connections"]["sha256"]:
            raise ContractError("Titan neuron: connection hashes differ")
        if capture["timing_export"]["output"]["sha256"] != manifest["inputs"]["timing"]["sha256"]:
            raise ContractError("Titan neuron: timing hashes differ")
        if capture["timing_export_binary"]["sha256"] != timing_build["binary"]["sha256"]:
            raise ContractError("Titan neuron: timing-export build provenance differs")
        if baseline["inputs"]["vpr"]["sha256"] != candidate["inputs"]["vpr"]["sha256"]:
            raise ContractError("Titan neuron: baseline/candidate VPR binaries differ")
        if baseline["inputs"]["vpr"]["sha256"] != capture["frozen_correctness_binary"]["sha256"]:
            raise ContractError("Titan neuron: QoR closure did not use frozen correctness VPR")
        if baseline["vpr_revision"] != candidate["vpr_revision"]:
            raise ContractError("Titan neuron: baseline/candidate VPR revisions differ")
        if (baseline["wirelength"], baseline["cpd_ns"], baseline["routing_iterations"]) != (
            766630,
            7.60292,
            15,
        ):
            raise ContractError("Titan neuron: same-router baseline did not reproduce frozen QoR")

        sdc_path = str((workspace / capture["source_inputs"]["sdc"]["path"]).resolve())
        for closure in (baseline, candidate):
            for option, expected in (
                ("--sdc_file", sdc_path),
                ("--router_lookahead", "map"),
                ("--initial_pres_fac", "1.0"),
                ("--router_profiler_astar_fac", "1.5"),
                ("--max_router_iterations", "400"),
            ):
                require_option(closure["command"], option, expected)

        row = {
            "case": "titan23_neuron",
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
        cohort_names = sorted({item["cohort"] for item in rows})
        architecture_cases = {
            "COFFE_22nm": [item for item in rows if item["case"] != "titan23_neuron"],
            "Titan23_Stratix_IV": [row],
        }
        report = {
            "schema": "TILEPLACE_TIMING_TITAN_EXTENDED_MATRIX_V1",
            "status": "pass",
            "date": "2026-09-01",
            "frozen_strategy": base["frozen_strategy"],
            "cases": rows,
            "aggregate": aggregate(rows),
            "cohort_aggregates": {
                name: aggregate([item for item in rows if item["cohort"] == name])
                for name in cohort_names
            },
            "architecture_aggregates": {
                name: aggregate(items) for name, items in architecture_cases.items()
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
                "connections": base["atom_timing_pin_mapping"]["connections"]
                + mapping["timed_connections"],
                "mapped": base["atom_timing_pin_mapping"]["mapped"]
                + mapping["atom_timing_pin_mapped"],
                "unmapped": base["atom_timing_pin_mapping"]["unmapped"],
                "strict_export_cases": base["atom_timing_pin_mapping"]["strict_export_cases"],
                "optional_export_cases": base["atom_timing_pin_mapping"]["optional_export_cases"] + 1,
            },
            "new_case_evidence": {
                "base_matrix": {"path": str(base_path), "sha256": sha256(base_path)},
                "manifest": {"path": str(manifest_path), "sha256": sha256(manifest_path)},
                "cpu": {"path": str(cpu_path), "sha256": sha256(cpu_path)},
                "candidate_place": {"path": str(place_path), "sha256": sha256(place_path)},
                "baseline_closure": {"path": str(baseline_path), "sha256": sha256(baseline_path)},
                "candidate_closure": {"path": str(candidate_path), "sha256": sha256(candidate_path)},
                "macro_capture": {"path": str(macro_path), "sha256": sha256(macro_path)},
                "input_capture": {"path": str(capture_path), "sha256": sha256(capture_path)},
                "timing_export_build": {
                    "path": str(timing_build_path),
                    "sha256": sha256(timing_build_path),
                },
            },
            "claim_boundary": (
                "Titan23 neuron is a post-freeze second-architecture-family validation point. It uses the "
                "unchanged 2x2/q60000 strategy and identical frozen VPR/SDC/router parameters for baseline "
                "and candidate. Its small routed-wirelength regression is retained. This remains CPU/VPR "
                "QoR evidence, not FPGA acceleration or hardware performance."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", **report["aggregate"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_timing_titan_extended_matrix: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
