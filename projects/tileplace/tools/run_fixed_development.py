#!/usr/bin/env python3
"""Validate one fixed implementation on the four already observed development cases."""

import argparse
import json
import math
import subprocess
import time
from pathlib import Path

from prepare_tileplace_v4_heldout_matrix import verify_search_audit
from run_v4_timing_protocol import signature, feedback_signature
from tileplace_provenance import verify_files
from tileplace_vpr import ContractError, dump_json, sha256


def validate(report_path, implementation):
    report = json.loads(report_path.read_text())
    if report["status"] != "pass" or report["provenance"]["implementation"]["sha256"] != implementation:
        raise ContractError("report implementation/status mismatch")
    verify_search_audit(report, report_path.parent.name)
    verify_files(report["provenance"]["implementation"]["sources"])
    verify_files(report["provenance"]["inputs"])
    if sha256(Path(report["output_place"]["path"])) != report["output_place"]["sha256"]:
        raise ContractError("final placement changed")
    if any(t["closure"].get("status") != "pass" or t["closure"].get("legal") is not True for t in report["trials"]):
        raise ContractError("native oracle failure; retain artifacts for diagnosis")
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--protocol", type=Path, required=True)
    parser.add_argument("--sha256", required=True)
    args = parser.parse_args()
    if sha256(args.protocol) != args.sha256:
        raise ContractError("protocol seal mismatch")
    protocol = json.loads(args.protocol.read_text())
    verify_files(protocol["files"])
    root = Path(protocol["output_root"])
    root.mkdir(parents=True, exist_ok=False)
    rows = []
    for case in protocol["cases"]:
        reports = []
        receipts = []
        for reused in case.get("retained_reports", []):
            path = Path(reused["path"])
            if sha256(path) != reused["sha256"]:
                raise ContractError("retained report changed")
            reports.append(validate(path, protocol["implementation_sha256"]))
            receipts.append(reused)
        for index in range(case["new_runs"]):
            run = root / case["case"] / f"run_{index:02d}"
            run.mkdir(parents=True)
            command = [v.replace("{run_dir}", str(run)) for v in case["command"]]
            dump_json(run / "command.json", command)
            print(f"START {case['case']} run {index}", flush=True)
            with (run / "stdout.log").open("w") as out, (run / "stderr.log").open("w") as err:
                start = time.perf_counter()
                process = subprocess.run(command, cwd=protocol["cwd"], stdout=out, stderr=err, check=False)
                wall = time.perf_counter() - start
            dump_json(run / "process.json", {"returncode": process.returncode, "process_wall_s": wall})
            if process.returncode:
                raise ContractError("development run failed; no automatic retries")
            path = run / "report.json"
            reports.append(validate(path, protocol["implementation_sha256"]))
            receipts.append({"path": str(path), "sha256": sha256(path)})
            print(f"DONE {case['case']} run {index}: {wall:.3f} s", flush=True)
        first = reports[0]
        for other in reports[1:]:
            if signature(first) != signature(other) or feedback_signature(first) != feedback_signature(other):
                raise ContractError("development repeat changed search or feedback")
            if first["phases"] != other["phases"] or [t["transactions"] for t in first["trials"]] != [t["transactions"] for t in other["trials"]]:
                raise ContractError("development repeat changed transaction costs")
        cpd = first["final"]["cpd_ns"] / first["baseline"]["cpd_ns"]
        wl = first["final"]["wirelength"] / first["baseline"]["wirelength"]
        rows.append({"case": case["case"], "reports": receipts, "repeat_count": len(reports),
                     "baseline": first["baseline"], "final": first["final"],
                     "closure_calls": first["closure_calls"], "accepted_transactions": first["accepted_transactions"],
                     "cpd_ratio": cpd, "wirelength_ratio": wl, "all_repeats_exact": True})
        dump_json(root / "progress.json", {"completed_cases": rows})
    result = {"schema": "TILEPLACE_FIXED_DEVELOPMENT_V1", "status": "pass",
              "protocol_sha256": args.sha256, "implementation_sha256": protocol["implementation_sha256"],
              "cases": rows,
              "cpd_geomean_change_pct": (math.exp(sum(math.log(r["cpd_ratio"]) for r in rows) / len(rows)) - 1) * 100,
              "wirelength_geomean_change_pct": (math.exp(sum(math.log(r["wirelength_ratio"]) for r in rows) / len(rows)) - 1) * 100,
              "limitations": protocol["limitations"]}
    dump_json(root / "summary.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "cases"}, sort_keys=True), flush=True)


if __name__ == "__main__":
    main()
