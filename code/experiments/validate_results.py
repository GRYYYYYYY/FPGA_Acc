#!/usr/bin/env python3
"""Validate legality, determinism, and QoR equivalence in an experiment directory."""

from __future__ import annotations

import argparse
import csv
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("result_dir", type=Path)
    parser.add_argument("--max-wirelength-delta-pct", type=float, default=2.0)
    args = parser.parse_args()

    with (args.result_dir / "summary.csv").open(encoding="utf-8", newline="") as stream:
        rows = list(csv.DictReader(stream))
    failures: list[str] = []
    for row in rows:
        name = f"{row['design']}/{row['variant']}"
        if row["all_legal"].lower() != "true":
            failures.append(f"{name}: illegal or failed route")
        if row["deterministic"].lower() != "true":
            failures.append(f"{name}: route hash is not deterministic")
        if abs(float(row["wirelength_delta_pct"])) > args.max_wirelength_delta_pct:
            failures.append(
                f"{name}: wirelength delta {row['wirelength_delta_pct']}% exceeds gate"
            )
    if failures:
        print("VALIDATION FAILED")
        for failure in failures:
            print(f"- {failure}")
        return 1
    print(f"VALIDATION PASS: {len(rows)} design/variant groups")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
