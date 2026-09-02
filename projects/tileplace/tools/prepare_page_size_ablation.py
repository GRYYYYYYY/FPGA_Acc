#!/usr/bin/env python3
"""Audit the 2x2, 4x4, and 8x8 page-size timing QoR ablation."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json


CASES = (
    ("diffeq", "diffeq_seed1_cw200"),
    ("frisc", "frisc_seed1_cw200"),
    ("elliptic", "elliptic_seed1_cw200"),
    ("clma", "clma_seed1_cw200"),
)


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
        sizes = []
        for size in (2, 4, 8):
            rows = []
            for short_name, directory_name in CASES:
                base_dir = experiments / directory_name
                endpoint_dir = experiments / f"{directory_name}_endpoints"
                baseline = load(base_dir / "vpr_native_closure.json")
                cpu = load(endpoint_dir / f"page{size}_connection_star_guard_q60000_w1.json")
                native_path = endpoint_dir / f"page{size}_connection_star_guard_q60000_w1_vpr_native.json"
                reused_from_page4 = False
                if native_path.is_file():
                    native = load(native_path)
                else:
                    page4_cpu = load(endpoint_dir / "page4_connection_star_guard_q60000_w1.json")
                    if cpu["output_place_sha256"] != page4_cpu["output_place_sha256"]:
                        raise ContractError(f"{short_name}/page{size}: missing closure for unique placement")
                    native = load(endpoint_dir / "page4_connection_star_guard_q60000_w1_vpr_native.json")
                    reused_from_page4 = True
                for evidence in (baseline, cpu, native):
                    if evidence.get("status") != "pass" or evidence.get("legal", True) is not True:
                        raise ContractError(f"{short_name}/page{size}: non-passing evidence")
                rows.append(
                    {
                        "case": short_name,
                        "placement_sha256": cpu["output_place_sha256"],
                        "native_evidence_reused_from_page4_by_hash": reused_from_page4,
                        "accepted_moves": cpu["accepted_moves"],
                        "wirelength": native["wirelength"],
                        "wirelength_delta_pct": delta(native["wirelength"], baseline["wirelength"]),
                        "cpd_ns": native["cpd_ns"],
                        "cpd_delta_pct": delta(native["cpd_ns"], baseline["cpd_ns"]),
                    }
                )
            aggregate = {
                "wirelength_geomean_delta_pct": (
                    math.prod(1.0 + row["wirelength_delta_pct"] / 100.0 for row in rows)
                    ** (1.0 / len(rows))
                    - 1.0
                ) * 100.0,
                "cpd_geomean_delta_pct": (
                    math.prod(1.0 + row["cpd_delta_pct"] / 100.0 for row in rows)
                    ** (1.0 / len(rows))
                    - 1.0
                ) * 100.0,
                "wirelength_worst_delta_pct": max(row["wirelength_delta_pct"] for row in rows),
                "cpd_worst_delta_pct": max(row["cpd_delta_pct"] for row in rows),
                "wirelength_improved_cases": sum(row["wirelength_delta_pct"] < 0 for row in rows),
            }
            sizes.append({"page_size": [size, size], "cases": rows, "aggregate": aggregate})
        best = min(sizes, key=lambda item: item["aggregate"]["wirelength_geomean_delta_pct"])
        if best["page_size"] != [2, 2]:
            raise ContractError("page-size selection changed; review the frozen recommendation")
        report = {
            "schema": "TILEPLACE_PAGE_SIZE_ABLATION_V1",
            "status": "pass",
            "date": "2026-08-31",
            "fixed_parameters": {
                "timing_model": "connection_star",
                "critical_distance_guard_q": 60000,
                "timing_weight": 1,
                "wire_weight": 256,
            },
            "sizes": sizes,
            "selected_page_size": [2, 2],
            "selection_rule": "minimum four-case routed-wirelength geomean delta; report CPD and worst case",
            "claim_boundary": "Page size was selected on this four-case matrix and requires validation on additional cases.",
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", "selected_page_size": [2, 2], **best["aggregate"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_page_size_ablation: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
