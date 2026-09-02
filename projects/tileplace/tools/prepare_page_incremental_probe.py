#!/usr/bin/env python3
"""Audit the first page-decomposed incremental placement QoR probe."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, sha256


def load(path: Path) -> dict:
    if not path.is_file():
        raise ContractError(f"missing evidence: {path}")
    return json.loads(path.read_text())


def delta(candidate: float, baseline: float) -> float:
    return (candidate / baseline - 1.0) * 100.0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.tileplace.resolve()
        experiments = root / "experiments"
        bigkey_dir = experiments / "bigkey_tight_seed3_cw300_v2"
        diffeq_dir = experiments / "diffeq_seed1_cw200"
        diffeq_endpoint_dir = experiments / "diffeq_seed1_cw200_endpoints"
        koios_dir = experiments / "koios_conv_layer_seed1_cw300"
        bigkey_external = load(bigkey_dir / "external_constraint_case.json")
        bigkey_cpu = load(bigkey_dir / "page4_incremental.json")
        bigkey_native = load(bigkey_dir / "page4_incremental_vpr_native.json")
        diffeq_baseline = load(diffeq_dir / "vpr_native_closure.json")
        diffeq_cpu = load(diffeq_dir / "page4_incremental.json")
        diffeq_native = load(diffeq_dir / "page4_incremental_vpr_native.json")
        diffeq_endpoint_manifest = load(diffeq_endpoint_dir / "manifest.json")
        diffeq_star_cpu = load(diffeq_endpoint_dir / "page4_connection_star_w1.json")
        diffeq_star_native = load(diffeq_endpoint_dir / "page4_connection_star_w1_vpr_native.json")
        diffeq_guard_cpu = load(
            diffeq_endpoint_dir / "page4_connection_star_guard_q60000_w1.json"
        )
        diffeq_guard_native = load(
            diffeq_endpoint_dir / "page4_connection_star_guard_q60000_w1_vpr_native.json"
        )
        koios_baseline = load(koios_dir / "vpr_native_closure.json")
        koios_cpu = load(koios_dir / "page4_incremental.json")
        koios_native = load(koios_dir / "page4_incremental_vpr_native.json")
        for evidence in (
            bigkey_external, bigkey_cpu, bigkey_native,
            diffeq_baseline, diffeq_cpu, diffeq_native, diffeq_star_cpu,
            diffeq_star_native, diffeq_guard_cpu, diffeq_guard_native,
            koios_baseline, koios_cpu, koios_native,
        ):
            if evidence.get("status") != "pass" or evidence.get("legal", True) is not True:
                raise ContractError("probe contains non-passing evidence")
        koios_repeat = root / "work/koios_page4_repeat.place"
        if sha256(koios_repeat) != koios_cpu["output_place_sha256"]:
            raise ContractError("Koios repeated output does not match the archived placement")
        if koios_native["placement_validation"]["macros"] != 43:
            raise ContractError("Koios native closure did not preserve all 43 macros")

        bigkey_base_wl = bigkey_external["baseline"]["wirelength"]
        bigkey_base_cpd = bigkey_external["baseline"]["cpd_ns"]
        koios_base_wl = koios_baseline["wirelength"]
        koios_base_cpd = koios_baseline["cpd_ns"]
        cases = [
            {
                "case": "bigkey_tight_seed3_cw300",
                "external_constraints": True,
                "macro_units": bigkey_cpu["macro_units"],
                "pages": bigkey_cpu["pages"],
                "accepted_moves": bigkey_cpu["accepted_moves"],
                "rejected_conflicts": bigkey_cpu["rejected_conflicts"],
                "internal_hpwl": [bigkey_cpu["initial_wire_hpwl"], bigkey_cpu["final_wire_hpwl"]],
                "baseline": {"wirelength": bigkey_base_wl, "cpd_ns": bigkey_base_cpd},
                "candidate": {
                    "wirelength": bigkey_native["wirelength"],
                    "cpd_ns": bigkey_native["cpd_ns"],
                    "wirelength_delta_pct": delta(bigkey_native["wirelength"], bigkey_base_wl),
                    "cpd_delta_pct": delta(bigkey_native["cpd_ns"], bigkey_base_cpd),
                },
                "decision": "reject_routed_wirelength_regression",
            },
            {
                "case": "diffeq_seed1_cw200",
                "external_constraints": False,
                "macro_units": diffeq_guard_cpu["macro_units"],
                "pages": diffeq_guard_cpu["pages"],
                "accepted_moves": diffeq_guard_cpu["accepted_moves"],
                "rejected_conflicts": diffeq_guard_cpu["rejected_conflicts"],
                "internal_hpwl": [
                    diffeq_guard_cpu["initial_wire_hpwl"], diffeq_guard_cpu["final_wire_hpwl"]
                ],
                "internal_timing_hpwl_q": [
                    diffeq_guard_cpu["initial_timing_hpwl_q"],
                    diffeq_guard_cpu["final_timing_hpwl_q"],
                ],
                "timing_refinement": {
                    "endpoint_mapping": diffeq_endpoint_manifest["connection_endpoint_mapping"],
                    "model": "criticality-weighted source/sink Manhattan distance",
                    "guard": {
                        "criticality_q": diffeq_guard_cpu["critical_distance_guard_q"],
                        "critical_distance_slack": diffeq_guard_cpu["critical_distance_slack"],
                        "guarded_connections": diffeq_guard_cpu["guarded_connections"],
                        "guarded_connections_increased": diffeq_guard_cpu[
                            "guarded_connections_increased"
                        ],
                    },
                    "native_ablation": {
                        "net_hpwl_cpd_ns": diffeq_native["cpd_ns"],
                        "connection_star_no_guard_cpd_ns": diffeq_star_native["cpd_ns"],
                        "connection_star_guard_cpd_ns": diffeq_guard_native["cpd_ns"],
                    },
                },
                "baseline": {
                    "routing_iterations": diffeq_baseline["routing_iterations"],
                    "wirelength": diffeq_baseline["wirelength"],
                    "cpd_ns": diffeq_baseline["cpd_ns"],
                },
                "candidate": {
                    "routing_iterations": diffeq_guard_native["routing_iterations"],
                    "wirelength": diffeq_guard_native["wirelength"],
                    "cpd_ns": diffeq_guard_native["cpd_ns"],
                    "wirelength_delta_pct": delta(
                        diffeq_guard_native["wirelength"], diffeq_baseline["wirelength"]
                    ),
                    "cpd_delta_pct": delta(
                        diffeq_guard_native["cpd_ns"], diffeq_baseline["cpd_ns"]
                    ),
                },
                "decision": "retain_timing_guard_candidate",
            },
            {
                "case": "koios_conv_layer_seed1_cw300",
                "external_constraints": False,
                "macro_units": koios_cpu["macro_units"],
                "pages": koios_cpu["pages"],
                "accepted_moves": koios_cpu["accepted_moves"],
                "rejected_conflicts": koios_cpu["rejected_conflicts"],
                "internal_hpwl": [koios_cpu["initial_wire_hpwl"], koios_cpu["final_wire_hpwl"]],
                "deterministic_output_sha256": koios_cpu["output_place_sha256"],
                "baseline": {
                    "routing_iterations": koios_baseline["routing_iterations"],
                    "wirelength": koios_base_wl,
                    "cpd_ns": koios_base_cpd,
                },
                "candidate": {
                    "routing_iterations": koios_native["routing_iterations"],
                    "wirelength": koios_native["wirelength"],
                    "cpd_ns": koios_native["cpd_ns"],
                    "wirelength_delta_pct": delta(koios_native["wirelength"], koios_base_wl),
                    "cpd_delta_pct": delta(koios_native["cpd_ns"], koios_base_cpd),
                },
                "decision": "retain_preliminary_candidate",
            },
        ]
        report = {
            "schema": "TILEPLACE_PAGE_INCREMENTAL_PROBE_V1",
            "status": "pass",
            "date": "2026-08-31",
            "algorithm": {
                "page_size": [4, 4],
                "page_colors": 4,
                "candidate_scope": "source page plus eight neighboring pages",
                "incremental_cost": "exact HPWL recomputation for touched nets",
                "timing_cost": "per-connection criticality-weighted source/sink Manhattan distance",
                "timing_guard": "input-relative distance cap for connections with criticality_q >= 60000",
                "conflict_protocol": koios_cpu["conflict_protocol"],
                "macro_protocol": "all macro members move as one proposal and one site/net transaction",
            },
            "cases": cases,
            "claim_boundary": (
                "This is a three-case algorithm probe, not a paper QoR matrix. On diffeq, the unguarded "
                "net-level and per-connection timing proxies both regressed native CPD; the calibrated "
                "critical-distance guard preserved baseline CPD while improving routed wirelength. Koios has "
                "no timing CSV in its current contract, and multi-case guard evidence is still required."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", "cases": len(cases), "koios_wirelength_delta_pct": cases[2]["candidate"]["wirelength_delta_pct"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_page_incremental_probe: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
