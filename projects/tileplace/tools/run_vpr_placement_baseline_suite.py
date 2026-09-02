#!/usr/bin/env python3
"""Run or resume a configured suite of VPR placement baselines."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path


def resolved(root: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (root / path).resolve()


def reusable_report(path: Path, case: dict[str, object], mode: str, config: dict[str, object]) -> bool:
    if not path.is_file():
        return False
    try:
        report = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError):
        return False
    return all(
        (
            report.get("schema") == "TILEPLACE_VPR_PLACEMENT_BASELINE_V1",
            report.get("status") == "pass",
            report.get("case") == case["case"],
            report.get("mode") == mode,
            report.get("seed") == case["seed"],
            report.get("channel_width") == case["channel_width"],
            report.get("inputs", {}).get("vpr", {}).get("sha256") == config["vpr_sha256"],
            report.get("tool_validation", {}).get("vpr_revision") == config["vpr_revision"],
        )
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, required=True)
    parser.add_argument("--work-root", type=Path, required=True)
    parser.add_argument("--report-root", type=Path, required=True)
    parser.add_argument("--runner", type=Path, required=True)
    parser.add_argument("--resume", action="store_true")
    args = parser.parse_args()

    config = json.loads(args.config.resolve().read_text())
    if config.get("schema") != "TILEPLACE_VPR_PLACEMENT_BASELINE_CASES_V1":
        raise SystemExit("unsupported placement baseline case schema")
    workspace = args.workspace_root.resolve()
    runner = args.runner.resolve()
    work_root = args.work_root.resolve()
    report_root = args.report_root.resolve()
    report_root.mkdir(parents=True, exist_ok=True)
    records = []
    for case in config["cases"]:
        for mode in ("conventional", "analytic"):
            report = report_root / f"{case['case']}_{mode}.json"
            work = work_root / f"vpr_placement_baseline_{case['case']}_{mode}_2026-08-31"
            if args.resume and reusable_report(report, case, mode, config):
                print(f"reuse {case['case']} {mode}: {report}", flush=True)
                records.append({"case": case["case"], "mode": mode, "action": "reused", "report": str(report)})
                continue
            command = [
                sys.executable,
                str(runner),
                "--mode", mode,
                "--case", str(case["case"]),
                "--contract", str(resolved(workspace, case["contract"])),
                "--vpr", str(resolved(workspace, config["vpr"])),
                "--architecture", str(resolved(workspace, case["architecture"])),
                "--circuit", str(resolved(workspace, case["circuit"])),
                "--netlist", str(resolved(workspace, case["netlist"])),
                "--reference-place", str(resolved(workspace, case["reference_place"])),
                "--work", str(work),
                "--report", str(report),
                "--seed", str(case["seed"]),
                "--channel-width", str(case["channel_width"]),
                "--expected-vpr-revision", str(config["vpr_revision"]),
                "--expected-vpr-sha256", str(config["vpr_sha256"]),
            ]
            print(f"run {case['case']} {mode}", flush=True)
            process = subprocess.run(command, cwd=workspace, text=True, stdout=subprocess.PIPE, check=False)
            if process.returncode != 0:
                print(process.stdout, file=sys.stderr)
                return process.returncode
            result = json.loads(process.stdout)
            print(
                f"pass {case['case']} {mode}: WL={result['wirelength']} "
                f"CPD={result['cpd_ns']} ns iterations={result['routing_iterations']}",
                flush=True,
            )
            records.append({"case": case["case"], "mode": mode, "action": "run", "report": str(report)})
    print(json.dumps({"status": "pass", "records": records}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
