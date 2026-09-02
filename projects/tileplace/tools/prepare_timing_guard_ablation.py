#!/usr/bin/env python3
"""Audit the diffeq connection-timing and critical-distance-guard ablation."""

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


def native_metrics(report: dict, baseline: dict) -> dict:
    return {
        "routing_iterations": report["routing_iterations"],
        "wirelength": report["wirelength"],
        "cpd_ns": report["cpd_ns"],
        "wirelength_delta_pct": delta(report["wirelength"], baseline["wirelength"]),
        "cpd_delta_pct": delta(report["cpd_ns"], baseline["cpd_ns"]),
    }


def cpu_metrics(report: dict) -> dict:
    return {
        "timing_model": report.get("timing_model", "net_hpwl"),
        "timing_weight": report["timing_weight"],
        "critical_distance_guard_q": report.get("critical_distance_guard_q", 0),
        "critical_distance_slack": report.get("critical_distance_slack", 0),
        "guarded_connections": report.get("guarded_connections", 0),
        "guarded_connections_increased": report.get("guarded_connections_increased"),
        "accepted_moves": report["accepted_moves"],
        "wire_hpwl": [report["initial_wire_hpwl"], report["final_wire_hpwl"]],
        "timing_cost_q": [report["initial_timing_hpwl_q"], report["final_timing_hpwl_q"]],
        "placement_sha256": report["output_place_sha256"],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.tileplace.resolve()
        experiments = root / "experiments"
        base_dir = experiments / "diffeq_seed1_cw200"
        endpoint_dir = experiments / "diffeq_seed1_cw200_endpoints"
        baseline = load(base_dir / "vpr_native_closure.json")
        net_hpwl_cpu = load(base_dir / "page4_incremental.json")
        net_hpwl_native = load(base_dir / "page4_incremental_vpr_native.json")
        unguarded_cpu = load(endpoint_dir / "page4_connection_star_w1.json")
        unguarded_native = load(endpoint_dir / "page4_connection_star_w1_vpr_native.json")
        guard55_cpu = load(endpoint_dir / "page4_connection_star_guard_q55000_w1.json")
        guard55_native = load(endpoint_dir / "page4_connection_star_guard_q55000_w1_vpr_native.json")
        guard60_cpu = load(endpoint_dir / "page4_connection_star_guard_q60000_w1.json")
        guard60_native = load(endpoint_dir / "page4_connection_star_guard_q60000_w1_vpr_native.json")
        guard60_w2 = load(endpoint_dir / "page4_connection_star_guard_q60000_w2.json")
        guard60_w4 = load(endpoint_dir / "page4_connection_star_guard_q60000_w4.json")
        manifest = load(endpoint_dir / "manifest.json")
        repeat = load(root / "work/diffeq_guard_q60000_repeat.json")

        evidence = (
            baseline, net_hpwl_cpu, net_hpwl_native, unguarded_cpu, unguarded_native,
            guard55_cpu, guard55_native, guard60_cpu, guard60_native, guard60_w2,
            guard60_w4, repeat,
        )
        if any(item.get("status") != "pass" or item.get("legal", True) is not True for item in evidence):
            raise ContractError("timing ablation contains non-passing evidence")
        mapping = manifest["connection_endpoint_mapping"]
        if mapping["timed_fully_mapped"] != mapping["timed_connections"]:
            raise ContractError("connection endpoint mapping is incomplete")
        selected_hash = guard60_cpu["output_place_sha256"]
        if repeat["output_place_sha256"] != selected_hash:
            raise ContractError("q60000 deterministic repeat differs from archived placement")
        for scaled in (guard60_w2, guard60_w4):
            if scaled["output_place_sha256"] != selected_hash:
                raise ContractError("timing-weight scale changed the q60000 placement")
        if sha256(endpoint_dir / "page4_connection_star_guard_q60000_w1.place") != selected_hash:
            raise ContractError("q60000 archived placement hash differs from its CPU report")
        if guard60_cpu["guarded_connections_increased"] != 0:
            raise ContractError("selected guard candidate increased a protected connection distance")
        if guard60_native["cpd_ns"] > baseline["cpd_ns"]:
            raise ContractError("selected guard candidate regresses native CPD")
        if guard60_native["wirelength"] >= baseline["wirelength"]:
            raise ContractError("selected guard candidate does not improve native wirelength")

        variants = [
            {
                "variant": "net_max_criticality_times_hpwl",
                "cpu": cpu_metrics(net_hpwl_cpu),
                "native": native_metrics(net_hpwl_native, baseline),
                "decision": "reject_cpd_regression",
            },
            {
                "variant": "connection_star_no_guard",
                "cpu": cpu_metrics(unguarded_cpu),
                "native": native_metrics(unguarded_native, baseline),
                "decision": "reject_cpd_regression",
            },
            {
                "variant": "connection_star_guard_q55000",
                "cpu": cpu_metrics(guard55_cpu),
                "native": native_metrics(guard55_native, baseline),
                "decision": "feasible_but_weaker_wirelength",
            },
            {
                "variant": "connection_star_guard_q60000",
                "cpu": cpu_metrics(guard60_cpu),
                "native": native_metrics(guard60_native, baseline),
                "decision": "select",
            },
        ]
        report = {
            "schema": "TILEPLACE_TIMING_GUARD_ABLATION_V1",
            "status": "pass",
            "date": "2026-08-31",
            "case": "diffeq_seed1_cw200",
            "endpoint_mapping": mapping,
            "baseline": {
                "routing_iterations": baseline["routing_iterations"],
                "wirelength": baseline["wirelength"],
                "cpd_ns": baseline["cpd_ns"],
            },
            "variants": variants,
            "selected": {
                "variant": "connection_star_guard_q60000",
                "criticality_fraction": 60000 / 65535,
                "deterministic_output_sha256": selected_hash,
                "repeat_match": True,
                "timing_weights_with_identical_placement": [1, 2, 4],
                "native": native_metrics(guard60_native, baseline),
            },
            "claim_boundary": (
                "This single-case ablation shows that the per-connection model alone did not protect CPD, "
                "while an input-relative Manhattan-distance guard on the highest-criticality connections "
                "preserved diffeq CPD and improved routed wirelength. Multi-case evidence is still required."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", "variants": len(variants), **report["selected"]["native"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_timing_guard_ablation: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
