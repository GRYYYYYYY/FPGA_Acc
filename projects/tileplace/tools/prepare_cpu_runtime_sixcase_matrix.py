#!/usr/bin/env python3
"""Merge audited development and post-freeze TilePlace CPU runtime samples."""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json, sha256


DEVELOPMENT_CASES = ("diffeq", "frisc", "elliptic", "clma")
VALIDATION_CASES = ("spmv", "softmax")


def load(path: Path) -> dict:
    if not path.is_file():
        raise ContractError(f"missing runtime evidence: {path}")
    return json.loads(path.read_text())


def scaling(cases: list[dict]) -> dict:
    connection_counts = [row["timed_connections"] for row in cases]
    median_walls = [row["wall_s"]["median"] for row in cases]
    mean_log_connections = statistics.mean(math.log(value) for value in connection_counts)
    mean_log_walls = statistics.mean(math.log(value) for value in median_walls)
    numerator = sum(
        (math.log(count) - mean_log_connections) * (math.log(wall) - mean_log_walls)
        for count, wall in zip(connection_counts, median_walls)
    )
    denominator = sum(
        (math.log(count) - mean_log_connections) ** 2 for count in connection_counts
    )
    return {
        "case_count": len(cases),
        "log_log_slope_median_wall_vs_timed_connections": numerator / denominator,
        "interpretation": "descriptive single-worker case scaling, not a complexity proof",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--development", type=Path, required=True)
    parser.add_argument("--validation", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        root = args.tileplace.resolve()
        sources = [args.development.resolve(), args.validation.resolve()]
        reports = [load(path) for path in sources]
        if any(report.get("status") != "pass" for report in reports):
            raise ContractError("runtime source report did not pass")

        protocol_keys = (
            "warmups", "measured_repetitions", "page_size", "timing_model",
            "critical_distance_guard_q", "proposal_workers",
            "eager_disabled_guard_costs", "included",
        )
        reference_protocol = reports[0]["protocol"]
        for report in reports[1:]:
            for key in protocol_keys:
                if report["protocol"].get(key) != reference_protocol.get(key):
                    raise ContractError(f"runtime protocol mismatch for {key}")
        environment_keys = ("cpu_model", "logical_cpus", "pinned_cpu", "pinned_cpus")
        for report in reports[1:]:
            for key in environment_keys:
                if report["environment"].get(key) != reports[0]["environment"].get(key):
                    raise ContractError(f"runtime environment mismatch for {key}")

        expected_sets = (set(DEVELOPMENT_CASES), set(VALIDATION_CASES))
        cases = []
        for report, expected, cohort in zip(
            reports, expected_sets, ("development", "post_freeze_validation")
        ):
            source_cases = {row["case"] for row in report["cases"]}
            if source_cases != expected:
                raise ContractError(
                    f"runtime source cases {sorted(source_cases)} != {sorted(expected)}"
                )
            for row in report["cases"]:
                if len(row["samples"]) != reference_protocol["measured_repetitions"]:
                    raise ContractError(f"{row['case']}: incomplete measured samples")
                candidate = load(
                    root / "experiments"
                    / f"{row['case']}_seed1_cw{300 if row['case'] in VALIDATION_CASES else 200}_endpoints"
                    / "page2_connection_star_guard_q60000_w1.json"
                )
                expected_hash = candidate["output_place_sha256"]
                if row["output_place_sha256"] != expected_hash or any(
                    sample["output_place_sha256"] != expected_hash for sample in row["samples"]
                ):
                    raise ContractError(f"{row['case']}: runtime placement hash mismatch")
                cases.append({**row, "cohort": cohort})
        order = {name: index for index, name in enumerate(DEVELOPMENT_CASES + VALIDATION_CASES)}
        cases.sort(key=lambda row: order[row["case"]])

        warmups = reference_protocol["warmups"]
        protocol = dict(reference_protocol)
        protocol["cache_state"] = (
            f"{warmups} warmups per case; measured runs are warm-cache"
        )
        medians = [row["wall_s"]["median"] for row in cases]
        report = {
            "schema": "TILEPLACE_CPU_RUNTIME_MATRIX_V2",
            "status": "pass",
            "sources": [
                {"path": str(path), "sha256": sha256(path)} for path in sources
            ],
            "environments": [source["environment"] for source in reports],
            "protocol": protocol,
            "cases": cases,
            "case_scaling": scaling(cases),
            "aggregate": {
                "cases": len(cases),
                "median_wall_s_min": min(medians),
                "median_wall_s_max": max(medians),
                "max_wall_cv": max(row["wall_s"]["cv"] for row in cases),
            },
            "claim_boundary": (
                "Pinned single-core Python reference runtime. The six cases were measured in two "
                "sequential batches under the same protocol and CPU model. This is not VPR "
                "end-to-end or FPGA performance evidence."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", **report["aggregate"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_cpu_runtime_sixcase_matrix: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
