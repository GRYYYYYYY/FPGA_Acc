#!/usr/bin/env python3
"""Run reproducible PersistRoute software experiments and emit raw JSON + CSV."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import platform
import statistics
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", type=Path, default=root / "experiments/configs/smoke.json")
    parser.add_argument("--exe", type=Path, default=root / "build/persist_route_sw.exe")
    parser.add_argument("--output-root", type=Path, default=root / "experiments/results")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = json.loads(args.config.read_text(encoding="utf-8"))
    if not args.exe.exists():
        raise SystemExit(f"executable not found: {args.exe}; run scripts/build.ps1 first")

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = args.output_root / f"{config['name']}_{stamp}"
    raw_dir = run_dir / "raw"
    raw_dir.mkdir(parents=True, exist_ok=False)
    manifest = {
        "schema_version": 1,
        "created_utc": stamp,
        "config": str(args.config.resolve()),
        "config_sha256": sha256(args.config),
        "executable": str(args.exe.resolve()),
        "executable_sha256": sha256(args.exe),
        "host": {"platform": platform.platform(), "python": sys.version},
    }
    (run_dir / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    rows: list[dict[str, object]] = []
    for design in config["designs"]:
        for variant in config["variants"]:
            hashes: list[str] = []
            for repetition in range(config["repetitions"]):
                raw_name = f"{design['name']}__{variant['name']}__r{repetition}.json"
                command = [
                    str(args.exe),
                    "--width", str(design["width"]),
                    "--height", str(design["height"]),
                    "--connections", str(design["connections"]),
                    "--capacity", str(design["capacity"]),
                    "--pattern", design["pattern"],
                    "--seed", str(design["seed"]),
                    "--iterations", str(config["router"]["iterations"]),
                    "--bbox-margin", str(config["router"]["bbox_margin"]),
                    "--mode", variant["mode"],
                    "--batch", str(variant["batch"]),
                    "--threads", str(variant["threads"]),
                ]
                completed = subprocess.run(command, capture_output=True, text=True, check=False)
                if completed.returncode not in (0, 2):
                    raise RuntimeError(
                        f"command failed ({completed.returncode}): {' '.join(command)}\n{completed.stderr}"
                    )
                payload = json.loads(completed.stdout)
                payload["runner"] = {
                    "repetition": repetition,
                    "return_code": completed.returncode,
                    "command": command,
                    "stderr": completed.stderr,
                }
                (raw_dir / raw_name).write_text(
                    json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
                )
                hashes.append(payload["result"]["route_hash"])
                rows.append({
                    "design": design["name"],
                    "variant": variant["name"],
                    "repetition": repetition,
                    "legal": payload["result"]["legal"],
                    "route_success": payload["result"]["route_success"],
                    "wirelength": payload["result"]["wirelength"],
                    "route_hash": payload["result"]["route_hash"],
                    **payload["metrics"],
                })
            if len(set(hashes)) != 1:
                raise RuntimeError(f"non-deterministic output: {design['name']} / {variant['name']}")

    fieldnames = list(rows[0].keys())
    with (run_dir / "runs.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    summary_rows: list[dict[str, object]] = []
    for design in config["designs"]:
        for variant in config["variants"]:
            group = [r for r in rows if r["design"] == design["name"] and r["variant"] == variant["name"]]
            summary_rows.append({
                "design": design["name"],
                "variant": variant["name"],
                "all_legal": all(bool(r["legal"]) for r in group),
                "deterministic": len({r["route_hash"] for r in group}) == 1,
                "wirelength": group[0]["wirelength"],
                "median_wall_ms": statistics.median(float(r["wall_ms"]) for r in group),
                "median_search_ms": statistics.median(float(r["search_ms"]) for r in group),
                "median_commit_ms": statistics.median(float(r["commit_ms"]) for r in group),
                "conflicts": group[0]["conflicts"],
                "replays": group[0]["replays"],
                "rollback_rate_pct": (
                    100.0 * float(group[0]["conflicts"]) / max(1.0, float(group[0]["searches"]))
                ),
                "iterations": group[0]["iterations"],
                "route_hash": group[0]["route_hash"],
            })

    serial_time = {
        row["design"]: float(row["median_wall_ms"])
        for row in summary_rows if row["variant"] == "serial"
    }
    serial_wl = {
        row["design"]: int(row["wirelength"])
        for row in summary_rows if row["variant"] == "serial"
    }
    for row in summary_rows:
        baseline_time = serial_time.get(str(row["design"]))
        baseline_wl = serial_wl.get(str(row["design"]))
        row["speedup_vs_serial"] = (
            baseline_time / float(row["median_wall_ms"])
            if baseline_time is not None and float(row["median_wall_ms"]) > 0 else ""
        )
        row["wirelength_delta_pct"] = (
            100.0 * (int(row["wirelength"]) - baseline_wl) / baseline_wl
            if baseline_wl else ""
        )
    with (run_dir / "summary.csv").open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(summary_rows[0].keys()))
        writer.writeheader()
        writer.writerows(summary_rows)

    print(run_dir)
    return 0 if all(bool(r["legal"]) for r in rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
