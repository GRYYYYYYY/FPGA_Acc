#!/usr/bin/env python3
"""Convert routed-connection CSV into patched-VPR reference timing input."""

from __future__ import annotations

import argparse
import csv
import json
import sys
from pathlib import Path

from tileplace_vpr import ContractError, sha256


FIELDS = (
    "iteration",
    "task_id",
    "net_id",
    "source",
    "sink",
    "routed",
    "delay_ps",
    "criticality_q",
)
REQUIRED_CONNECTION_FIELDS = ("id", "net_id", "source", "sink", "criticality_q")
REFERENCE_ITERATION = 0xFFFFFFFF


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--connections", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--report", type=Path, required=True)
    args = parser.parse_args()
    try:
        connections = args.connections.resolve()
        if not connections.is_file():
            raise ContractError(f"missing connections CSV: {connections}")
        output = args.output.resolve()
        report_path = args.report.resolve()
        output.parent.mkdir(parents=True, exist_ok=True)
        report_path.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_suffix(output.suffix + ".tmp")
        rows = 0
        expected_id = 0
        with connections.open(encoding="utf-8-sig", newline="") as source, temporary.open(
            "w", encoding="utf-8", newline=""
        ) as target:
            reader = csv.DictReader(source)
            missing = [field for field in REQUIRED_CONNECTION_FIELDS if field not in (reader.fieldnames or ())]
            if missing:
                raise ContractError("connections CSV missing fields: " + ", ".join(missing))
            writer = csv.writer(target)
            writer.writerow(FIELDS)
            for row in reader:
                task_id = int(row["id"])
                if task_id != expected_id:
                    raise ContractError(
                        f"connection task IDs must be dense: expected {expected_id}, got {task_id}"
                    )
                values = (row["net_id"], row["source"], row["sink"], row["criticality_q"])
                if any(int(value) < 0 for value in values):
                    raise ContractError(f"connection {task_id} has a negative numeric field")
                writer.writerow(
                    (
                        REFERENCE_ITERATION,
                        task_id,
                        row["net_id"],
                        row["source"],
                        row["sink"],
                        0,
                        0,
                        row["criticality_q"],
                    )
                )
                rows += 1
                expected_id += 1
        if rows == 0:
            raise ContractError("connections CSV has no rows")
        temporary.replace(output)
        report = {
            "schema": "TILEPLACE_REFERENCE_TIMING_INPUT_V1",
            "status": "pass",
            "reference_iteration": REFERENCE_ITERATION,
            "rows": rows,
            "connections": {"path": str(connections), "sha256": sha256(connections)},
            "output": {"path": str(output), "sha256": sha256(output)},
        }
        report_path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
        print(json.dumps({"status": "pass", "rows": rows, "sha256": sha256(output)}, sort_keys=True))
        return 0
    except (ContractError, OSError, ValueError, KeyError, csv.Error) as error:
        print(f"prepare_reference_timing_input: ERROR: {error}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
