#!/usr/bin/env python3
"""Benchmark the frozen TilePlace CPU research flow on pinned logical CPUs."""

from __future__ import annotations

import argparse
import gc
import json
import math
import os
import platform
import resource
import statistics
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from tileplace_research import optimize
from tileplace_vpr import ContractError, dump_json, sha256


CASES = (
    ("diffeq", "diffeq_seed1_cw200", "persistroute/experiments/vpr9/baseline_runs/vpr_serial/diffeq_seed1_cw200/diffeq.place"),
    ("frisc", "frisc_seed1_cw200", "persistroute/experiments/vpr9/baseline_runs/vpr_serial/frisc_seed1_cw200/frisc.place"),
    ("elliptic", "elliptic_seed1_cw200", "persistroute/experiments/vpr9/baseline_runs/vpr_serial/elliptic_seed1_cw200/elliptic.place"),
    ("clma", "clma_seed1_cw200", "persistroute/experiments/vpr9/baseline_runs/vpr_serial/clma_seed1_cw200/clma.place"),
    ("spmv", "spmv_seed1_cw300", "persistroute/experiments/balanced_pathreads_matrix_2026-08-28/koios_spmv_seed1_cw300/input/reference/spmv.pre-vpr.place"),
    ("softmax", "softmax_seed1_cw300", "persistroute/experiments/balanced_pathreads_matrix_2026-08-28/koios_softmax_seed1_cw300/input/reference/softmax.pre-vpr.place"),
)


def load(path: Path) -> dict:
    if not path.is_file():
        raise ContractError(f"missing benchmark input: {path}")
    return json.loads(path.read_text())


def stats(values: list[float]) -> dict[str, float]:
    median = statistics.median(values)
    return {
        "min": min(values),
        "median": median,
        "mean": statistics.mean(values),
        "max": max(values),
        "pstdev": statistics.pstdev(values),
        "cv": statistics.pstdev(values) / statistics.mean(values),
        "median_absolute_deviation": statistics.median(abs(value - median) for value in values),
    }


def usage_delta(before: resource.struct_rusage, after: resource.struct_rusage) -> dict[str, float | int]:
    return {
        "user_s": after.ru_utime - before.ru_utime,
        "system_s": after.ru_stime - before.ru_stime,
        "minor_faults": after.ru_minflt - before.ru_minflt,
        "major_faults": after.ru_majflt - before.ru_majflt,
        "input_blocks": after.ru_inblock - before.ru_inblock,
        "output_blocks": after.ru_oublock - before.ru_oublock,
        "voluntary_context_switches": after.ru_nvcsw - before.ru_nvcsw,
        "involuntary_context_switches": after.ru_nivcsw - before.ru_nivcsw,
    }


def run_once(
    contract: Path,
    input_place: Path,
    output_place: Path,
    output_report: Path,
    proposal_workers: int,
    eager_disabled_guard_costs: bool,
) -> tuple[dict, dict]:
    gc.collect()
    usage_before = resource.getrusage(resource.RUSAGE_SELF)
    process_before = time.process_time_ns()
    wall_before = time.perf_counter_ns()
    report = optimize(
        contract,
        input_place,
        output_place,
        2,
        2,
        8,
        64,
        256,
        1,
        "connection_star",
        60000,
        0,
        None,
        None,
        proposal_workers,
        eager_disabled_guard_costs,
    )
    dump_json(output_report, report)
    wall_after = time.perf_counter_ns()
    process_after = time.process_time_ns()
    usage_after = resource.getrusage(resource.RUSAGE_SELF)
    sample = {
        "wall_s": (wall_after - wall_before) / 1.0e9,
        "process_s": (process_after - process_before) / 1.0e9,
        "usage": usage_delta(usage_before, usage_after),
        "output_place_sha256": report["output_place_sha256"],
        "accepted_moves": report["accepted_moves"],
    }
    return report, sample


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--tileplace", type=Path, default=Path(__file__).parents[1])
    parser.add_argument("--work", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--warmups", type=int, default=1)
    parser.add_argument("--repetitions", type=int, default=7)
    parser.add_argument("--cpu", type=int, default=0)
    parser.add_argument("--cpu-list", help="comma-separated logical CPUs; overrides --cpu")
    parser.add_argument("--proposal-workers", type=int, default=1)
    parser.add_argument("--eager-disabled-guard-costs", action="store_true")
    parser.add_argument("--cases", default=",".join(case[0] for case in CASES))
    args = parser.parse_args()
    try:
        if args.warmups < 1 or args.repetitions < 3:
            raise ContractError("benchmark requires at least one warmup and three measured repetitions")
        if args.proposal_workers < 1:
            raise ContractError("proposal workers must be positive")
        available = os.sched_getaffinity(0)
        pinned_cpus = (
            {int(value) for value in args.cpu_list.split(",")}
            if args.cpu_list
            else {args.cpu}
        )
        if not pinned_cpus or not pinned_cpus.issubset(available):
            raise ContractError(
                f"requested CPUs {sorted(pinned_cpus)} are outside process affinity {sorted(available)}"
            )
        if args.proposal_workers > len(pinned_cpus):
            raise ContractError("proposal workers exceed the pinned CPU count")
        os.sched_setaffinity(0, pinned_cpus)
        selected_cases = {value.strip() for value in args.cases.split(",") if value.strip()}
        known_cases = {case[0] for case in CASES}
        if not selected_cases or not selected_cases.issubset(known_cases):
            raise ContractError(f"unknown or empty case selection: {sorted(selected_cases)}")
        root = args.tileplace.resolve()
        work = args.work.resolve()
        work.mkdir(parents=True, exist_ok=True)
        case_reports = []
        for short_name, directory_name, place_path in CASES:
            if short_name not in selected_cases:
                continue
            contract = root / "experiments" / f"{directory_name}_endpoints"
            input_place = root.parent / place_path
            archived = load(contract / "page2_connection_star_guard_q60000_w1.json")
            expected_hash = archived["output_place_sha256"]
            for warmup in range(args.warmups):
                report, _sample = run_once(
                    contract,
                    input_place,
                    work / f"{short_name}.warmup{warmup}.place",
                    work / f"{short_name}.warmup{warmup}.json",
                    args.proposal_workers,
                    args.eager_disabled_guard_costs,
                )
                if report["output_place_sha256"] != expected_hash:
                    raise ContractError(f"{short_name}: warmup placement differs from frozen result")
            samples = []
            final_report = None
            for repetition in range(args.repetitions):
                final_report, sample = run_once(
                    contract,
                    input_place,
                    work / f"{short_name}.run{repetition}.place",
                    work / f"{short_name}.run{repetition}.json",
                    args.proposal_workers,
                    args.eager_disabled_guard_costs,
                )
                if sample["output_place_sha256"] != expected_hash:
                    raise ContractError(f"{short_name}: measured placement differs from frozen result")
                samples.append(sample)
            assert final_report is not None
            wall_values = [sample["wall_s"] for sample in samples]
            process_values = [sample["process_s"] for sample in samples]
            wall_summary = stats(wall_values)
            case_reports.append(
                {
                    "case": short_name,
                    "blocks": final_report["blocks"],
                    "nets_with_multiple_blocks": final_report["nets_with_multiple_blocks"],
                    "timed_connections": final_report["timed_connections"],
                    "accepted_moves": final_report["accepted_moves"],
                    "input_place_sha256": sha256(input_place),
                    "output_place_sha256": expected_hash,
                    "samples": samples,
                    "wall_s": wall_summary,
                    "process_s": stats(process_values),
                    "median_blocks_per_s": final_report["blocks"] / wall_summary["median"],
                    "median_timed_connections_per_s": (
                        final_report["timed_connections"] / wall_summary["median"]
                    ),
                }
            )
        scaling = None
        if len(case_reports) >= 2:
            connection_counts = [row["timed_connections"] for row in case_reports]
            median_walls = [row["wall_s"]["median"] for row in case_reports]
            mean_log_connections = statistics.mean(math.log(value) for value in connection_counts)
            mean_log_walls = statistics.mean(math.log(value) for value in median_walls)
            numerator = sum(
                (math.log(count) - mean_log_connections) * (math.log(wall) - mean_log_walls)
                for count, wall in zip(connection_counts, median_walls)
            )
            denominator = sum(
                (math.log(count) - mean_log_connections) ** 2 for count in connection_counts
            )
            scaling = {
                "log_log_slope_median_wall_vs_timed_connections": numerator / denominator,
                "case_count": len(case_reports),
                "interpretation": "descriptive single-worker case scaling, not a complexity proof",
            }
        cpu_model = "unknown"
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                cpu_model = line.split(":", 1)[1].strip()
                break
        report = {
            "schema": "TILEPLACE_CPU_RUNTIME_MATRIX_V1",
            "status": "pass",
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "environment": {
                "platform": platform.platform(),
                "python": sys.version,
                "cpu_model": cpu_model,
                "logical_cpus": os.cpu_count(),
                "pinned_cpu": next(iter(pinned_cpus)) if len(pinned_cpus) == 1 else None,
                "pinned_cpus": sorted(pinned_cpus),
                "affinity": sorted(os.sched_getaffinity(0)),
                "loadavg_after": os.getloadavg(),
            },
            "protocol": {
                "warmups": args.warmups,
                "measured_repetitions": args.repetitions,
                "page_size": [2, 2],
                "timing_model": "connection_star",
                "critical_distance_guard_q": 60000,
                "proposal_workers": args.proposal_workers,
                "eager_disabled_guard_costs": args.eager_disabled_guard_costs,
                "included": "contract load, optimization, placement write, legality validation, and JSON report write",
                "cache_state": f"{args.warmups} warmups per case; measured runs are warm-cache",
            },
            "cases": case_reports,
            "case_scaling": scaling,
            "claim_boundary": (
                "Python CPU reference with deterministic fork-process proposal evaluation on the "
                "recorded pinned logical CPUs. This is not VPR end-to-end or FPGA performance evidence."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(
            json.dumps(
                {
                    "status": "pass",
                    "cases": len(case_reports),
                    "median_wall_s": {
                        row["case"]: row["wall_s"]["median"] for row in case_reports
                    },
                    "proposal_workers": args.proposal_workers,
                    "case_scaling": scaling,
                },
                sort_keys=True,
            )
        )
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"benchmark_tileplace_research: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
