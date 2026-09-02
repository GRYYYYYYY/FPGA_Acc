#!/usr/bin/env python3
"""Audit fork-process proposal determinism and the clma worker scaling probe."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json


CASES = (
    ("diffeq", "diffeq_seed1_cw200"),
    ("frisc", "frisc_seed1_cw200"),
    ("elliptic", "elliptic_seed1_cw200"),
    ("clma", "clma_seed1_cw200"),
)
WORKERS = (1, 2, 4, 8)
EXACT_KEYS = (
    "output_place_sha256",
    "accepted_moves",
    "rejected_conflicts",
    "rejected_guard_candidates",
    "rejected_wire_candidates",
    "rejected_connection_wire_candidates",
    "max_rejected_guard_overrun",
    "final_objective",
    "final_wire_hpwl",
    "final_timing_hpwl_q",
    "passes",
)


def load(path: Path) -> dict:
    if not path.is_file():
        raise ContractError(f"missing parallel evidence: {path}")
    return json.loads(path.read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.tileplace.resolve()
        determinism = []
        for short_name, directory_name in CASES:
            serial = load(
                root / "experiments" / f"{directory_name}_endpoints"
                / "page2_connection_star_guard_q60000_w1.json"
            )
            if serial.get("status") != "pass" or serial.get("legal") is not True:
                raise ContractError(f"{short_name}: serial reference did not pass")
            row = {
                "case": short_name,
                "serial_output_place_sha256": serial["output_place_sha256"],
                "workers": [],
            }
            for workers in WORKERS[1:]:
                parallel = load(root / "work" / f"{directory_name}_parallel{workers}_audit.json")
                if parallel.get("status") != "pass" or parallel.get("legal") is not True:
                    raise ContractError(f"{short_name}/{workers}: parallel run did not pass")
                mismatches = [key for key in EXACT_KEYS if serial.get(key) != parallel.get(key)]
                if mismatches:
                    raise ContractError(
                        f"{short_name}/{workers}: serial/parallel mismatch in {mismatches}"
                    )
                row["workers"].append(
                    {
                        "proposal_workers": workers,
                        "backend": parallel["proposal_parallel_backend"],
                        "exact_match": True,
                    }
                )
            determinism.append(row)

        scaling_reports = {
            workers: load(root / "work" / f"clma_persistent_scaling_w{workers}.json")
            for workers in WORKERS
        }
        serial_median = scaling_reports[1]["cases"][0]["wall_s"]["median"]
        scaling = []
        output_hash = None
        for workers in WORKERS:
            report = scaling_reports[workers]
            if report.get("status") != "pass" or len(report.get("cases", [])) != 1:
                raise ContractError(f"clma/{workers}: invalid scaling report")
            if report["protocol"]["proposal_workers"] != workers:
                raise ContractError(f"clma/{workers}: protocol worker count mismatch")
            case = report["cases"][0]
            if case["case"] != "clma":
                raise ContractError(f"clma/{workers}: wrong benchmark case")
            if output_hash is None:
                output_hash = case["output_place_sha256"]
            if case["output_place_sha256"] != output_hash:
                raise ContractError("clma scaling changed the placement hash")
            if {
                sample["output_place_sha256"] for sample in case["samples"]
            } != {output_hash}:
                raise ContractError(f"clma/{workers}: measured samples are not deterministic")
            median = case["wall_s"]["median"]
            speedup = serial_median / median
            scaling.append(
                {
                    "proposal_workers": workers,
                    "pinned_cpus": report["environment"]["pinned_cpus"],
                    "wall_s": case["wall_s"],
                    "samples": case["samples"],
                    "speedup": speedup,
                    "parallel_efficiency": speedup / workers,
                }
            )
        best = max(scaling, key=lambda row: row["speedup"])
        report = {
            "schema": "TILEPLACE_PARALLEL_PROPOSAL_MATRIX_V1",
            "status": "pass",
            "date": "2026-08-31",
            "algorithm": (
                "read-only snapshot proposal evaluation in Linux fork processes; deterministic "
                "delta/color/unit commit remains in the parent process"
            ),
            "determinism": {
                "cases": determinism,
                "case_count": len(determinism),
                "worker_counts": list(WORKERS),
                "all_exact": True,
            },
            "clma_scaling": {
                "protocol": scaling_reports[1]["protocol"],
                "environment": scaling_reports[1]["environment"],
                "points": scaling,
                "best_workers": best["proposal_workers"],
                "best_speedup": best["speedup"],
                "decision": "correct_parallel_semantics_but_no_controlled_process_scaling_speedup",
                "root_cause": (
                    "persistent workers avoid per-pass fork, but Python snapshot serialization, "
                    "process IPC, and memory traffic dominate these problem sizes"
                ),
            },
            "claim_boundary": (
                "The 1/2/4/8-worker paths are result-equivalent on four cases. The largest-case "
                "speedup is reported as a prototype result and does not support a scalable CPU or "
                "FPGA acceleration claim."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "deterministic_cases": len(determinism),
                    "best_workers": best["proposal_workers"],
                    "best_speedup": best["speedup"],
                },
                sort_keys=True,
            )
        )
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_parallel_proposal_matrix: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
