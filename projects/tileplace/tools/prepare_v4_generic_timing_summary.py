#!/usr/bin/env python3
"""Combine all three preregistered observations after the comparator amendment."""

import argparse
import json
import statistics
from pathlib import Path

from prepare_tileplace_v4_heldout_matrix import verify_search_audit
from run_v4_timing_protocol import signature, feedback_signature
from tileplace_provenance import verify_files
from tileplace_vpr import ContractError, dump_json, sha256


PROTOCOLS = (
    ("tileplace_v4_generic_timing_protocol_2026-09-29.json", "295d41a8ac371b65c1961cb7f85b77a060fb95398a1f4a2fd7b6334a048b9517"),
    ("tileplace_v4_generic_timing_continuation_protocol_2026-09-29.json", "3b129ba72e7d855dfdf8990a3892aeff51d12a7c2f349f1002da945168741165"),
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    exp = Path(__file__).resolve().parents[1] / "experiments"
    protocols = []
    for name, expected in PROTOCOLS:
        path = exp / name
        if sha256(path) != expected:
            raise ContractError(f"timing protocol hash mismatch: {path}")
        protocols.append(json.loads(path.read_text()))
    original, continuation = protocols
    if original["implementation_sha256"] != continuation["implementation_sha256"]:
        raise ContractError("production implementation changed across the amendment")
    verify_files(continuation["amendment"]["retained_runs"])
    completed = json.loads((Path(continuation["output_root"]) / "summary.json").read_text())
    if completed["status"] != "pass" or len(completed["runs"]) != 2:
        raise ContractError("continuation did not finish both observations")
    directories = [(Path(original["output_root"]) / "run_00", True),
                   (Path(original["output_root"]) / "run_01", False)]
    directories.extend((Path(continuation["output_root"]) / f"run_{i:02d}", False) for i in range(2))
    reference = None
    reference_feedback = None
    expected_search = signature(json.loads(Path(original["reference_report"]).read_text()))
    rows = []
    for directory, warmup in directories:
        report_path, timing_path = directory / "report.json", directory / "timing.json"
        report = json.loads(report_path.read_text())
        timing = json.loads(timing_path.read_text())
        process = json.loads((directory / "process.json").read_text())
        if process["returncode"] != 0 or timing["report"]["sha256"] != sha256(report_path):
            raise ContractError("observation did not complete or timing/report binding changed")
        provenance = report["provenance"]
        if provenance["implementation"]["sha256"] != original["implementation_sha256"]:
            raise ContractError("observation uses a different production implementation")
        # A completed implementation may no longer be the worktree version.
        # Verify its retained bytes instead of requiring worktree immutability.
        archive_path = exp / "implementation_sources" / provenance["implementation"]["sha256"] / "archive.json"
        if archive_path.exists():
            archive = json.loads(archive_path.read_text())
            expected_sources = {(r["name"], r["sha256"]) for r in provenance["implementation"]["sources"]}
            if {(r["name"], r["sha256"]) for r in archive["sources"]} != expected_sources:
                raise ContractError("archived source set differs from observed implementation")
            verify_files(archive["sources"])
        else:
            verify_files(provenance["implementation"]["sources"])
        verify_files(provenance["inputs"])
        verify_search_audit(report, "diffeq")
        if sha256(directory / "final.place") != report["output_place"]["sha256"]:
            raise ContractError("final placement changed")
        current, feedback = signature(report), feedback_signature(report)
        if current != expected_search:
            raise ContractError("observation differs from the registered generic reference trajectory")
        if reference is None:
            reference, reference_feedback = current, feedback
        elif current != reference or feedback != reference_feedback:
            raise ContractError("repeated decisions or feedback content differ")
        rows.append({"directory": str(directory), "warmup": warmup,
                     "process_wall_s": process["process_wall_s"],
                     "flow_wall_s": timing["flow_wall_s"],
                     "preparation_wall_s": timing["preparation_wall_s"],
                     "search_stage_wall_s": timing["search_stage_wall_s"],
                     "report_sha256": sha256(report_path), "timing_sha256": sha256(timing_path)})
    measured = [r for r in rows if not r["warmup"]]
    times = [r["process_wall_s"] for r in measured]
    if len(measured) != 3:
        raise ContractError("expected exactly three retained measured observations")
    result = {
        "schema": "TILEPLACE_V4_GENERIC_DEVELOPMENT_TIMING_COMBINED_V1", "status": "pass",
        "case": "diffeq", "implementation_sha256": original["implementation_sha256"],
        "protocols": [{"file": n, "sha256": h} for n, h in PROTOCOLS], "runs": rows,
        "median_process_wall_s": statistics.median(times),
        "sample_cv_pct": 100 * statistics.stdev(times) / statistics.mean(times),
        "median_stage_wall_s": {stage: statistics.median(r["search_stage_wall_s"][stage] for r in measured)
                                for stage in measured[0]["search_stage_wall_s"]},
        "median_stage_fraction_of_process": {stage: statistics.median(r["search_stage_wall_s"][stage] / r["process_wall_s"] for r in measured)
                                             for stage in measured[0]["search_stage_wall_s"]},
        "final": reference["final"], "final_place_sha256": reference["final_place_sha256"],
        "closure_calls": reference["closure_calls"], "accepted_transactions": reference["accepted_transactions"],
        "all_search_and_feedback_identities_equal": True,
        "limitations": original["limitations"] + ["Comparator amendment excludes path-bearing raw artifact hashes; all three measured observations retained"],
    }
    dump_json(args.output, result)
    print(json.dumps({k: v for k, v in result.items() if k != "runs"}, sort_keys=True))


if __name__ == "__main__":
    main()
