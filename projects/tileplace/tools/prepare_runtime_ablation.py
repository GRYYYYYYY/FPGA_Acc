#!/usr/bin/env python3
"""Audit the disabled-guard cost-elision runtime ablation."""

from __future__ import annotations

import argparse
import json
import math
import sys
from pathlib import Path

from tileplace_vpr import ContractError, dump_json


def load(path: Path) -> dict:
    if not path.is_file():
        raise ContractError(f"missing runtime evidence: {path}")
    return json.loads(path.read_text())


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before", type=Path, required=True)
    parser.add_argument("--after", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        before = load(args.before.resolve())
        after = load(args.after.resolve())
        for label, report in (("before", before), ("after", after)):
            if report.get("schema") != "TILEPLACE_CPU_RUNTIME_MATRIX_V1":
                raise ContractError(f"{label}: unexpected runtime schema")
            if report.get("status") != "pass":
                raise ContractError(f"{label}: runtime matrix did not pass")
        protocol_keys = (
            "warmups", "measured_repetitions", "page_size", "timing_model",
            "critical_distance_guard_q", "included", "cache_state",
        )
        for key in protocol_keys:
            if before["protocol"][key] != after["protocol"][key]:
                raise ContractError(f"runtime protocols differ at {key}")
        if before["protocol"].get("proposal_workers", 1) != after["protocol"].get(
            "proposal_workers", 1
        ):
            raise ContractError("runtime protocols use different proposal-worker counts")
        if before["protocol"].get("eager_disabled_guard_costs") is not True:
            raise ContractError("before matrix did not enable eager disabled-guard costs")
        if after["protocol"].get("eager_disabled_guard_costs") is not False:
            raise ContractError("after matrix did not disable eager disabled-guard costs")
        for key in ("cpu_model", "pinned_cpu", "affinity"):
            if before["environment"][key] != after["environment"][key]:
                raise ContractError(f"runtime environments differ at {key}")
        before_by_case = {row["case"]: row for row in before["cases"]}
        after_by_case = {row["case"]: row for row in after["cases"]}
        if set(before_by_case) != set(after_by_case):
            raise ContractError("runtime matrices have different cases")
        rows = []
        for case in sorted(before_by_case):
            old = before_by_case[case]
            new = after_by_case[case]
            if old["output_place_sha256"] != new["output_place_sha256"]:
                raise ContractError(f"{case}: optimization changed the placement")
            for label, evidence in (("before", old), ("after", new)):
                hashes = {sample["output_place_sha256"] for sample in evidence["samples"]}
                if hashes != {evidence["output_place_sha256"]}:
                    raise ContractError(f"{case}: {label} samples are not deterministic")
            speedup = old["wall_s"]["median"] / new["wall_s"]["median"]
            rows.append(
                {
                    "case": case,
                    "blocks": new["blocks"],
                    "timed_connections": new["timed_connections"],
                    "output_place_sha256": new["output_place_sha256"],
                    "before_median_wall_s": old["wall_s"]["median"],
                    "after_median_wall_s": new["wall_s"]["median"],
                    "before_wall_cv": old["wall_s"]["cv"],
                    "after_wall_cv": new["wall_s"]["cv"],
                    "speedup": speedup,
                }
            )
        report = {
            "schema": "TILEPLACE_RUNTIME_GUARD_ELISION_ABLATION_V1",
            "status": "pass",
            "change": (
                "skip touched-net HPWL and unweighted connection-wire before-costs when their "
                "candidate guards are disabled"
            ),
            "environment": after["environment"],
            "protocol": after["protocol"],
            "cases": rows,
            "aggregate": {
                "geomean_speedup": math.prod(row["speedup"] for row in rows) ** (1.0 / len(rows)),
                "min_speedup": min(row["speedup"] for row in rows),
                "max_speedup": max(row["speedup"] for row in rows),
                "max_after_wall_cv": max(row["after_wall_cv"] for row in rows),
            },
            "claim_boundary": (
                "This is a same-process single-core Python implementation ablation with warm caches. "
                "It is not thread scaling, end-to-end VPR speedup, or FPGA performance."
            ),
        }
        dump_json(args.output.resolve(), report)
        print(json.dumps({"status": "pass", **report["aggregate"]}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, json.JSONDecodeError) as error:
        print(f"prepare_runtime_ablation: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
